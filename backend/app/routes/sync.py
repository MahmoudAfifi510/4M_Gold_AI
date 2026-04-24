from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.market_data_service import MarketDataService


router = APIRouter(tags=["data-sync"])
market_service = MarketDataService()


@router.post("/fetch-historical-data")
def fetch_historical_data(db: Session = Depends(get_db)):
    try:
        result = market_service.fetch_historical_data(db, sync_type="manual-historical")
        return {"message": "Historical market data synchronized.", **result}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
