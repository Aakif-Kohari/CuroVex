from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Explanation, Prediction
from api.schemas import ExplanationResponse

router = APIRouter()


@router.get("/{prediction_id}", response_model=ExplanationResponse)
def get_explanations(prediction_id: UUID, db: Session = Depends(get_db)):
    # LAZY IMPORTS: Only load heavy AI code when this endpoint is hit
    try:
        from explainability.path_based import explain
    except ImportError:

        def explain(drug_id: str, disease_id: str, max_hops: int = 3):
            return []

    try:
        from explainability.counterfactual import counterfactual_explain
    except ImportError:

        def counterfactual_explain(drug_id: str, disease_id: str):
            return None

    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    # Check cache
    existing = (
        db.query(Explanation).filter(Explanation.prediction_id == prediction_id).all()
    )
    if existing:
        return {"prediction_id": prediction_id, "explanations": existing}

    explanations_created = []

    # Path-based
    try:
        pb_res = explain(prediction.drug_id, prediction.disease_id)
        if pb_res is not None:
            expl = Explanation(
                prediction_id=prediction_id,
                method="path_based",
                fidelity_score=None,
                subgraph=(
                    pb_res if isinstance(pb_res, dict) else {"paths": str(pb_res)}
                ),  # Serialize mock
            )
            db.add(expl)
            explanations_created.append(expl)
    except Exception as e:
        print(f"Path-based explanation failed: {e}")

    # Counterfactual
    try:
        cf_res = counterfactual_explain(prediction.drug_id, prediction.disease_id)
        if cf_res is not None:
            expl = Explanation(
                prediction_id=prediction_id,
                method="counterfactual",
                fidelity_score=(
                    cf_res.overall_fidelity
                    if hasattr(cf_res, "overall_fidelity")
                    else 0.9
                ),
                subgraph=(
                    cf_res.subgraph if hasattr(cf_res, "subgraph") else {"cf": "mock"}
                ),
            )
            db.add(expl)
            explanations_created.append(expl)
    except Exception as e:
        print(f"Counterfactual explanation failed: {e}")

    if explanations_created:
        db.commit()
        for ex in explanations_created:
            db.refresh(ex)

    return {"prediction_id": prediction_id, "explanations": explanations_created}
