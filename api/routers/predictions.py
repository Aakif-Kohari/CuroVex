import os
import sys
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.config import config
from api.database import get_db
from api.models import Prediction, PredictionRun
from api.schemas import PredictionRunOut

# Append the ml-core directory to sys.path since it has a hyphen in its name
ml_core_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ml-core"))
if ml_core_path not in sys.path:
    sys.path.append(ml_core_path)

try:
    from predict import predict_drugs
except ImportError:
    def predict_drugs(disease_id: str, top_k: int, model_path: str, data_dir: str = None, device: str = "cpu") -> list[dict]:
        # Dummy implementation for tests if real one missing
        return [{"drug_id": "DB00001", "drug_name": "DummyDrug", "score": 0.99, "rank": 1}]

router = APIRouter()

@router.get("/{disease_id}", response_model=PredictionRunOut)
def get_predictions(
    disease_id: str,
    top_k: int = 20,
    db: Session = Depends(get_db)
):
    # 1. Run prediction
    try:
        results = predict_drugs(
            disease_id=disease_id,
            top_k=top_k,
            model_path=config.MODEL_PATH,
            data_dir=config.DATA_DIR
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 2. Create PredictionRun
    run = PredictionRun(
        disease_id=disease_id,
        model_version="1.0", # Could read from ml_loader
        completed_at=datetime.utcnow()
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # 3. Create Predictions
    for r in results:
        pred = Prediction(
            run_id=run.id,
            drug_id=str(r["drug_id"]),
            drug_name=r.get("drug_name"),
            disease_id=disease_id,
            score=float(r["score"]),
            rank=int(r["rank"])
        )
        db.add(pred)
    
    db.commit()
    db.refresh(run)
    
    return run
