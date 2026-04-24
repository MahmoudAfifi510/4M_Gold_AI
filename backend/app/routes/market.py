from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.schema import HistoricalMarketData
from app.schemas.market import MarketDataRead
from app.services.market_data_service import MarketDataService


router = APIRouter(prefix="/market", tags=["market"])
market_service = MarketDataService()


@router.post("/sync")
def sync_market_data(db: Session = Depends(get_db)):
    try:
        result = market_service.sync_today(db, sync_type="manual-sync")
        return {"message": "Market data synchronized.", **result}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/latest", response_model=MarketDataRead)
def latest_market_data(db: Session = Depends(get_db)):
    row = db.execute(
        select(HistoricalMarketData).order_by(HistoricalMarketData.market_date.desc()).limit(1)
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="No market data available.")
    return {
        "market_date": row.market_date,
        "gold_price": float(row.gold_price),
        "oil_price": float(row.oil_price),
        "usd_index": float(row.usd_index),
    }


@router.get("/admin/status")
def market_admin_status(db: Session = Depends(get_db)):
    return market_service.status(db)


@router.get("/history")
def market_history(
    period: str = Query(default="1m", pattern="^(1m|6m|1y)$"),
    db: Session = Depends(get_db),
):
    try:
        frame = market_service.load_history_range(db, period)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "period": period,
        "points": [
            {"market_date": row["market_date"], "gold_price": float(row["gold_price"])}
            for row in frame.to_dict(orient="records")
        ],
    }
