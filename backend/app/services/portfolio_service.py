from __future__ import annotations

from datetime import date
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.schema import GoldSaleTransaction, GoldTransaction, HistoricalMarketData


class PortfolioService:
    def _nearest_spot_price(self, session: Session, transaction_date: date) -> float:
        row = session.execute(
            select(HistoricalMarketData)
            .where(HistoricalMarketData.market_date <= transaction_date)
            .order_by(HistoricalMarketData.market_date.desc())
            .limit(1)
        ).scalar_one_or_none()
        if row is None:
            row = session.execute(
                select(HistoricalMarketData)
                .order_by(HistoricalMarketData.market_date.asc())
                .limit(1)
            ).scalar_one_or_none()
        if row is None:
            raise RuntimeError("No historical market data available.")
        return float(row.gold_price)

    def add_buy_transaction(
        self,
        session: Session,
        user_id: int,
        weight_oz: float,
        karat: int,
        price: float,
        transaction_date: date,
    ) -> GoldTransaction:
        if transaction_date > date.today():
            raise ValueError("Purchase date cannot be in the future.")
        if weight_oz <= 0:
            raise ValueError("Weight must be greater than zero.")

        txn = GoldTransaction(
            user_id=user_id,
            weight_oz=weight_oz,
            remaining_weight_oz=weight_oz,
            karat=karat,
            price=price,
            transaction_date=transaction_date,
        )
        session.add(txn)
        session.commit()
        session.refresh(txn)
        return txn

    def sell_from_buy(
        self,
        session: Session,
        user_id: int,
        buy_transaction_id: int,
        sell_weight_oz: float,
        price: float,
        transaction_date: date,
    ) -> GoldSaleTransaction:
        if transaction_date > date.today():
            raise ValueError("Sale date cannot be in the future.")
        if sell_weight_oz <= 0:
            raise ValueError("Sell weight must be greater than zero.")

        buy_txn = session.execute(
            select(GoldTransaction)
            .where(GoldTransaction.id == buy_transaction_id)
            .where(GoldTransaction.user_id == user_id)
        ).scalar_one_or_none()
        if buy_txn is None:
            raise ValueError("Referenced buy transaction was not found.")

        remaining_weight = float(buy_txn.remaining_weight_oz)
        if sell_weight_oz > remaining_weight:
            raise ValueError("Cannot sell more than the remaining owned amount.")

        unit_cost = float(buy_txn.price) / float(buy_txn.weight_oz)
        cost_basis = unit_cost * sell_weight_oz
        profit_loss = float(price) - cost_basis

        sell_txn = GoldSaleTransaction(
            user_id=user_id,
            buy_transaction_id=buy_transaction_id,
            sell_weight_oz=sell_weight_oz,
            price=price,
            profit_loss=profit_loss,
            transaction_date=transaction_date,
        )
        buy_txn.remaining_weight_oz = remaining_weight - sell_weight_oz
        session.add(sell_txn)
        session.commit()
        session.refresh(sell_txn)
        return sell_txn

    def list_buys(self, session: Session, user_id: int) -> list[dict]:
        rows = session.execute(
            select(GoldTransaction)
            .where(GoldTransaction.user_id == user_id)
            .order_by(GoldTransaction.transaction_date.desc(), GoldTransaction.id.desc())
        ).scalars().all()

        results = []
        for row in rows:
            remaining_weight = float(row.remaining_weight_oz)
            if remaining_weight <= 0:
                continue
            spot_price = self._nearest_spot_price(session, row.transaction_date)
            fineness = row.karat / 24.0
            unit_cost = float(row.price) / float(row.weight_oz)
            current_value = remaining_weight * fineness * spot_price
            remaining_cost_basis = unit_cost * remaining_weight
            unrealized_profit_loss = current_value - remaining_cost_basis
            sold_weight = float(row.weight_oz) - remaining_weight
            results.append(
                {
                    "id": row.id,
                    "weight_oz": float(row.weight_oz),
                    "remaining_weight_oz": remaining_weight,
                    "sold_weight_oz": sold_weight,
                    "karat": row.karat,
                    "price": float(row.price),
                    "transaction_date": row.transaction_date,
                    "spot_price": round(spot_price, 3),
                    "current_value": round(current_value, 3),
                    "unrealized_profit_loss": round(unrealized_profit_loss, 3),
                }
            )
        return results

    def list_sales(self, session: Session, user_id: int) -> list[dict]:
        rows = session.execute(
            select(GoldSaleTransaction)
            .where(GoldSaleTransaction.user_id == user_id)
            .order_by(GoldSaleTransaction.transaction_date.desc(), GoldSaleTransaction.id.desc())
        ).scalars().all()

        results = []
        for row in rows:
            buy_txn = session.execute(
                select(GoldTransaction).where(GoldTransaction.id == row.buy_transaction_id)
            ).scalar_one_or_none()
            results.append(
                {
                    "id": row.id,
                    "buy_transaction_id": row.buy_transaction_id,
                    "sell_weight_oz": float(row.sell_weight_oz),
                    "price": float(row.price),
                    "profit_loss": float(row.profit_loss),
                    "transaction_date": row.transaction_date,
                    "buy_weight_oz": float(buy_txn.weight_oz) if buy_txn else None,
                    "buy_karat": buy_txn.karat if buy_txn else None,
                }
            )
        return results

    def summary(self, session: Session, user_id: int) -> dict:
        buys = self.list_buys(session, user_id)
        sales = self.list_sales(session, user_id)
        total_realized_profit_loss = round(sum(sell["profit_loss"] for sell in sales), 3)
        total_unrealized_profit_loss = round(sum(buy["unrealized_profit_loss"] for buy in buys), 3)
        return {
            "total_profit_loss": total_realized_profit_loss,
            "total_realized_profit_loss": total_realized_profit_loss,
            "total_unrealized_profit_loss": total_unrealized_profit_loss,
            "buys": buys,
            "sales": sales,
        }

    def clear_user_data(self, session: Session, user_id: int) -> None:
        buy_ids = session.execute(
            select(GoldTransaction.id).where(GoldTransaction.user_id == user_id)
        ).scalars().all()

        session.execute(delete(GoldSaleTransaction).where(GoldSaleTransaction.user_id == user_id))
        if buy_ids:
            session.execute(delete(GoldTransaction).where(GoldTransaction.user_id == user_id))
        session.commit()
