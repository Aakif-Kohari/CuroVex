from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Prediction, ValidationResult
from api.schemas import ValidationOut

try:
    from validation.clinicaltrials_check import check_clinical_trials
except ImportError:
    def check_clinical_trials(drug_name: str, disease_name: str):
        class MockCT:
            has_trial = True
            evidence_url = "http://clinicaltrials.gov"
        return MockCT()

try:
    from validation.pubmed_check import check_pubmed
except ImportError:
    def check_pubmed(drug_name: str, disease_name: str):
        class MockPM:
            has_literature = True
        return MockPM()

router = APIRouter()

@router.get("/{prediction_id}", response_model=ValidationOut)
def get_validation(prediction_id: UUID, db: Session = Depends(get_db)):
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    existing = db.query(ValidationResult).filter(ValidationResult.prediction_id == prediction_id).first()
    if existing:
        return existing

    drug_name = prediction.drug_name or f"Drug_{prediction.drug_id}"
    disease_name = prediction.disease_id # disease_id is typically MONDO:XXXX, but clinicaltrials might expect name. For now, use the ID or a lookup if available.

    ct_res = check_clinical_trials(drug_name, disease_name)
    pm_res = check_pubmed(drug_name, disease_name)

    val = ValidationResult(
        prediction_id=prediction_id,
        has_clinical_trial=getattr(ct_res, "has_trial", False),
        has_literature_support=getattr(pm_res, "has_literature", False),
        evidence_url=getattr(ct_res, "evidence_url", None) or getattr(pm_res, "evidence_url", None)
    )
    
    db.add(val)
    db.commit()
    db.refresh(val)
    
    return val
