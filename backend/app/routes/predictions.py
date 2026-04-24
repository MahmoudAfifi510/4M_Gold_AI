from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import get_settings
from app.schemas.prediction import PredictionResponse
from app.services.model_service import ModelService

router = APIRouter(prefix="/predictions", tags=["predictions"])
model_service = ModelService()
settings = get_settings()


@router.get("/next-5-days", response_model=PredictionResponse)
def next_five_days(db: Session = Depends(get_db)):
    try:
        predictions = model_service.predict_next_days(db, days=5)
        return {"generated_at": datetime.now(settings.local_timezone).date(), "predictions": predictions}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
