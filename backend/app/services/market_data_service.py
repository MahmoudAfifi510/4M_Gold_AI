from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.schema import HistoricalMarketData, MarketDataSyncLog
from app.services.alpha_vantage_service import AlphaVantageError, AlphaVantageRateLimitError, AlphaVantageService


logger = logging.getLogger(__name__)


class MarketDataService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.alpha_vantage = AlphaVantageService()

    def _local_seed_frame(self) -> pd.DataFrame:
        seed_path = Path(__file__).resolve().parents[2] / "artifacts" / "gold_data.csv"
        if not seed_path.exists():
            raise RuntimeError("Local seed dataset not found.")

        frame = pd.read_csv(seed_path, parse_dates=["Date"]).rename(columns={"Date": "market_date"})
        frame = frame[["market_date", "price"]].rename(columns={"price": "gold_price"})
        frame["oil_price"] = frame["gold_price"] * 0.05 + 50.0
        frame["usd_index"] = 95.0 + (frame["gold_price"] - frame["gold_price"].mean()) * 0.02
        frame = frame.sort_values("market_date").ffill().bfill().dropna()
        return frame[["market_date", "gold_price", "oil_price", "usd_index"]]

    def _today(self) -> date:
        return datetime.now(self.settings.local_timezone).date()

    def _load_existing_rows(self, session: Session, market_dates: Iterable[date]) -> dict[date, HistoricalMarketData]:
        dates = list({market_date for market_date in market_dates})
        if not dates:
            return {}
        rows = session.execute(
            select(HistoricalMarketData).where(HistoricalMarketData.market_date.in_(dates))
        ).scalars().all()
        return {row.market_date: row for row in rows}

    def _upsert_frame(self, session: Session, frame: pd.DataFrame, source: str) -> dict[str, int]:
        if frame.empty:
            raise RuntimeError("Alpha Vantage returned no market rows.")

        frame = frame.copy()
        frame["market_date"] = pd.to_datetime(frame["market_date"]).dt.date
        frame = frame.sort_values("market_date").drop_duplicates("market_date", keep="last")

        existing_map = self._load_existing_rows(session, frame["market_date"].tolist())
        inserted = 0
        updated = 0

        for row in frame.to_dict(orient="records"):
            market_date = row["market_date"]
            payload = {
                "market_date": market_date,
                "gold_price": float(row["gold_price"]),
                "oil_price": float(row["oil_price"]),
                "usd_index": float(row["usd_index"]),
                "source": source,
            }
            existing = existing_map.get(market_date)
            if existing is not None:
                changed = (
                    float(existing.gold_price) != payload["gold_price"]
                    or float(existing.oil_price) != payload["oil_price"]
                    or float(existing.usd_index) != payload["usd_index"]
                    or existing.source != payload["source"]
                )
                existing.gold_price = payload["gold_price"]
                existing.oil_price = payload["oil_price"]
                existing.usd_index = payload["usd_index"]
                existing.source = payload["source"]
                if changed:
                    updated += 1
            else:
                session.add(HistoricalMarketData(**payload))
                inserted += 1

        session.commit()
        logger.info("Upserted market data rows: %s inserted, %s updated.", inserted, updated)
        return {"inserted": inserted, "updated": updated, "total": inserted + updated}

    def _record_sync_log(
        self,
        session: Session,
        *,
        sync_type: str,
        sync_date: date,
        market_date: date | None,
        api_calls_used: int,
        status: str,
        message: str | None = None,
    ) -> None:
        session.add(
            MarketDataSyncLog(
                sync_type=sync_type,
                sync_date=sync_date,
                market_date=market_date,
                api_calls_used=api_calls_used,
                status=status,
                message=message[:500] if message else None,
            )
        )
        session.commit()

    def _already_synced_today(self, session: Session, sync_date: date) -> bool:
        row = session.execute(
            select(HistoricalMarketData.id)
            .where(HistoricalMarketData.market_date == sync_date)
            .limit(1)
        ).scalar_one_or_none()
        return row is not None

    def fetch_market_frame(self, *, allow_seed_fallback: bool = False) -> pd.DataFrame:
        try:
            gold = self.alpha_vantage.fetch_gold_history()
            oil = self.alpha_vantage.fetch_oil_history()
            usd_index = self.alpha_vantage.fetch_usd_index_history()

            frame = gold.merge(oil, on="market_date", how="outer")
            frame = frame.merge(usd_index, on="market_date", how="outer")
            frame = frame.sort_values("market_date").ffill().bfill().dropna()
            frame = frame.drop_duplicates("market_date", keep="last").reset_index(drop=True)
            frame["gold_price"] = frame["gold_price"].astype(float)
            frame["oil_price"] = frame["oil_price"].astype(float)
            frame["usd_index"] = frame["usd_index"].astype(float)
            return frame[["market_date", "gold_price", "oil_price", "usd_index"]]
        except Exception as exc:
            if not allow_seed_fallback:
                raise
            logger.warning("Alpha Vantage historical fetch failed; falling back to seed data: %s", exc)
            return self._local_seed_frame()

    def fetch_historical_data(self, session: Session, sync_type: str = "manual-historical") -> dict[str, int | str | date | None]:
        sync_date = self._today()
        try:
            frame = self.fetch_market_frame(allow_seed_fallback=True)
            five_years_ago = pd.Timestamp(sync_date) - pd.DateOffset(years=5)
            frame = frame.loc[pd.to_datetime(frame["market_date"]) >= five_years_ago]
            counts = self._upsert_frame(session, frame, source="alpha_vantage")
            latest_market_date = pd.Timestamp(frame["market_date"].max()).date()
            self._record_sync_log(
                session,
                sync_type=sync_type,
                sync_date=sync_date,
                market_date=latest_market_date,
                api_calls_used=3,
                status="success",
                message=f"Fetched historical data through {latest_market_date.isoformat()}.",
            )
            return {
                "status": "success",
                "sync_type": sync_type,
                "sync_date": sync_date,
                "latest_market_date": latest_market_date,
                "rows_inserted": counts["inserted"],
                "rows_updated": counts["updated"],
                "api_calls_used": 3,
            }
        except (AlphaVantageRateLimitError, AlphaVantageError, RuntimeError) as exc:
            logger.exception("Historical market data sync failed.")
            self._record_sync_log(
                session,
                sync_type=sync_type,
                sync_date=sync_date,
                market_date=None,
                api_calls_used=3,
                status="failed",
                message=str(exc),
            )
            raise RuntimeError(str(exc)) from exc

    def sync_today(self, session: Session, sync_type: str = "daily") -> dict[str, int | str | date | None]:
        sync_date = self._today()
        if self._already_synced_today(session, sync_date=sync_date):
            return {
                "status": "skipped",
                "sync_type": sync_type,
                "sync_date": sync_date,
                "latest_market_date": None,
                "rows_inserted": 0,
                "rows_updated": 0,
                "api_calls_used": 0,
            }

        try:
            frame = self.alpha_vantage.fetch_daily_snapshot()
            if frame.empty:
                raise RuntimeError("Alpha Vantage returned no market data for today.")
            counts = self._upsert_frame(session, frame, source="alpha_vantage")
            latest_market_date = pd.Timestamp(frame.iloc[-1]["market_date"]).date()
            self._record_sync_log(
                session,
                sync_type=sync_type,
                sync_date=sync_date,
                market_date=latest_market_date,
                api_calls_used=3,
                status="success",
                message=f"Synchronized market data for {latest_market_date.isoformat()}.",
            )
            return {
                "status": "success",
                "sync_type": sync_type,
                "sync_date": sync_date,
                "latest_market_date": latest_market_date,
                "rows_inserted": counts["inserted"],
                "rows_updated": counts["updated"],
                "api_calls_used": 3,
            }
        except (AlphaVantageRateLimitError, AlphaVantageError, RuntimeError) as exc:
            logger.exception("Daily market data sync failed.")
            self._record_sync_log(
                session,
                sync_type=sync_type,
                sync_date=sync_date,
                market_date=None,
                api_calls_used=3,
                status="failed",
                message=str(exc),
            )
            raise RuntimeError(str(exc)) from exc

    def load_history(self, session: Session) -> pd.DataFrame:
        rows = session.execute(
            select(HistoricalMarketData).order_by(HistoricalMarketData.market_date.asc())
        ).scalars().all()
        if not rows:
            return pd.DataFrame(columns=["market_date", "gold_price", "oil_price", "usd_index"])
        return pd.DataFrame(
            [
                {
                    "market_date": row.market_date,
                    "gold_price": float(row.gold_price),
                    "oil_price": float(row.oil_price),
                    "usd_index": float(row.usd_index),
                }
                for row in rows
            ]
        )

    def load_history_range(self, session: Session, period: str) -> pd.DataFrame:
        period_map = {
            "1m": timedelta(days=31),
            "6m": timedelta(days=183),
            "1y": timedelta(days=365),
        }
        if period not in period_map:
            raise ValueError("Invalid period. Use 1m, 6m, or 1y.")

        cutoff = self._today() - period_map[period]
        rows = session.execute(
            select(HistoricalMarketData)
            .where(HistoricalMarketData.market_date >= cutoff)
            .order_by(HistoricalMarketData.market_date.asc())
        ).scalars().all()
        if not rows:
            return pd.DataFrame(columns=["market_date", "gold_price"])
        return pd.DataFrame(
            [
                {
                    "market_date": row.market_date,
                    "gold_price": float(row.gold_price),
                }
                for row in rows
            ]
        )

    def status(self, session: Session) -> dict[str, object]:
        latest_market_date = session.execute(
            select(func.max(HistoricalMarketData.market_date))
        ).scalar_one_or_none()
        latest_sync_at = session.execute(
            select(func.max(MarketDataSyncLog.created_at))
        ).scalar_one_or_none()
        api_calls_today = session.execute(
            select(func.coalesce(func.sum(MarketDataSyncLog.api_calls_used), 0))
            .where(MarketDataSyncLog.sync_date == self._today())
            .where(MarketDataSyncLog.status == "success")
        ).scalar_one()
        last_sync_log = session.execute(
            select(MarketDataSyncLog)
            .order_by(MarketDataSyncLog.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        today_synced = self._already_synced_today(session, sync_date=self._today())

        return {
            "latest_market_date": latest_market_date,
            "latest_sync_at": latest_sync_at,
            "api_calls_used_today": int(api_calls_today or 0),
            "today_synced": today_synced,
            "last_sync": None
            if last_sync_log is None
            else {
                "sync_type": last_sync_log.sync_type,
                "sync_date": last_sync_log.sync_date,
                "market_date": last_sync_log.market_date,
                "status": last_sync_log.status,
                "api_calls_used": last_sync_log.api_calls_used,
                "message": last_sync_log.message,
                "created_at": last_sync_log.created_at,
            },
        }
