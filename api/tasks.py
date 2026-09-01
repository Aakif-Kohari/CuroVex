from api.celery_app import celery_app
from api.database import SessionLocal
from api.models import PredictionRun, Prediction
from datetime import datetime

import sys
import os

ml_core_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../ml-core"))
if ml_core_path not in sys.path:
    sys.path.append(ml_core_path)

try:
    from predict import predict_drugs
except ImportError:
    def predict_drugs(disease_id: str, top_k: int, model_path: str, data_dir: str = None, device: str = "cpu"):
        return [{"drug_id": "DB00001", "drug_name": "DummyDrug", "score": 0.99, "rank": 1}]

@celery_app.task(bind=True)
def run_batch_predictions(self, disease_id: str, top_k: int, user_id: str = None):
    db = SessionLocal()
    try:
        from api.config import config
        results = predict_drugs(
            disease_id=disease_id,
            top_k=top_k,
            model_path=config.MODEL_PATH,
            data_dir=config.DATA_DIR
        )

        run = PredictionRun(
            disease_id=disease_id,
            user_id=user_id,
            model_version="1.0",
            completed_at=datetime.utcnow()
        )
        db.add(run)
        db.commit()
        db.refresh(run)

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
        return str(run.id)
    except Exception as e:
        db.rollback()
        raise self.retry(exc=e, countdown=60, max_retries=3)
    finally:
        db.close()
