from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.routes.dependencies import get_current_user
from app.schemas.portfolio import BuyTransactionCreate, PortfolioSummary, SellTransactionCreate
from app.services.portfolio_service import PortfolioService


router = APIRouter(prefix="/portfolio", tags=["portfolio"])
portfolio_service = PortfolioService()


@router.post("/buys")
def add_buy_transaction(
    payload: BuyTransactionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        txn = portfolio_service.add_buy_transaction(
            db,
            current_user.id,
            payload.weight_oz,
            payload.karat,
            payload.price,
            payload.transaction_date,
        )
        return {"message": "Buy transaction saved successfully.", "id": txn.id}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/transactions")
def add_buy_transaction_legacy(
    payload: BuyTransactionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return add_buy_transaction(payload, db, current_user)


@router.post("/buys/{buy_transaction_id}/sell")
def sell_from_buy(
    buy_transaction_id: int,
    payload: SellTransactionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        txn = portfolio_service.sell_from_buy(
            db,
            current_user.id,
            buy_transaction_id,
            payload.sell_weight_oz,
            payload.price,
            payload.transaction_date,
        )
        return {"message": "Sell transaction saved successfully.", "id": txn.id}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/transactions")
def list_transactions_legacy(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return list_buys(db, current_user)


@router.get("/buys")
def list_buys(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return {"buys": portfolio_service.list_buys(db, current_user.id)}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/sales")
def list_sales(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return {"sales": portfolio_service.list_sales(db, current_user.id)}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/summary", response_model=PortfolioSummary)
def summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return portfolio_service.summary(db, current_user.id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.delete("/data")
def clear_portfolio_data(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        portfolio_service.clear_user_data(db, current_user.id)
        return {"message": "Portfolio data cleared successfully."}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
