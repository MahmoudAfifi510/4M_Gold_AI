from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.core.config import get_settings
from app.db.session import Base, SessionLocal, engine
from app.models import schema as models  # noqa: F401
from app.routes.auth import router as auth_router
from app.routes.market import router as market_router
from app.routes.portfolio import router as portfolio_router
from app.routes.predictions import router as predictions_router
from app.routes.sync import router as sync_router
from app.services.market_data_service import MarketDataService
from app.services.model_service import ModelService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
market_service = MarketDataService()
model_service = ModelService()


def _migrate_legacy_market_schema() -> None:
    inspector = inspect(engine)
    if "historical_market_data" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("historical_market_data")}
    with engine.begin() as connection:
        if "usd_index" not in columns and "usd_price" in columns:
            connection.execute(
                text(
                    "ALTER TABLE historical_market_data "
                    "CHANGE COLUMN usd_price usd_index DECIMAL(18,6) NOT NULL"
                )
            )
            columns.add("usd_index")
        if "source" in columns:
            connection.execute(
                text(
                    "ALTER TABLE historical_market_data "
                    "MODIFY COLUMN source VARCHAR(50) NOT NULL DEFAULT 'alpha_vantage'"
                )
            )


def _migrate_legacy_portfolio_schema() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "gold_transactions" not in tables or "gold_buy_transactions" not in tables:
        return

    buy_count = 0
    with engine.begin() as connection:
        buy_count = connection.execute(text("SELECT COUNT(*) FROM gold_buy_transactions")).scalar_one()
        if buy_count:
            return

        legacy_rows = connection.execute(
            text(
                "SELECT id, user_id, weight_grams, karat, price, transaction_date "
                "FROM gold_transactions WHERE transaction_type = 'buy' ORDER BY id ASC"
            )
        ).mappings().all()
        if not legacy_rows:
            return

        ounces_per_gram = 1 / 28.349523125
        for row in legacy_rows:
            weight_oz = float(row["weight_grams"]) * ounces_per_gram
            connection.execute(
                text(
                    "INSERT INTO gold_buy_transactions "
                    "(id, user_id, weight_oz, remaining_weight_oz, karat, price, transaction_date, created_at) "
                    "VALUES (:id, :user_id, :weight_oz, :remaining_weight_oz, :karat, :price, :transaction_date, NOW())"
                ),
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "weight_oz": weight_oz,
                    "remaining_weight_oz": weight_oz,
                    "karat": row["karat"],
                    "price": row["price"],
                    "transaction_date": row["transaction_date"],
                },
            )


async def _daily_market_sync_loop() -> None:
    while True:
        await asyncio.sleep(24 * 60 * 60)
        db = SessionLocal()
        try:
            result = market_service.sync_today(db, sync_type="daily")
            logger.info("Scheduled market sync result: %s", result)
        except Exception as exc:  # pragma: no cover - background safety
            logger.exception("Scheduled market sync failed: %s", exc)
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _migrate_legacy_market_schema()
    _migrate_legacy_portfolio_schema()
    db = SessionLocal()
    sync_task: asyncio.Task | None = None
    try:
        if settings.auto_sync_on_startup:
            try:
                result = market_service.sync_today(db, sync_type="startup")
                logger.info("Startup market sync result: %s", result)
            except Exception as exc:
                logger.exception("Market sync skipped on startup: %s", exc)
        if settings.auto_train_on_startup:
            try:
                model_service.train(db)
            except Exception as exc:
                logger.exception("Model training skipped on startup: %s", exc)
        sync_task = asyncio.create_task(_daily_market_sync_loop())
    finally:
        db.close()
    try:
        yield
    finally:
        if sync_task is not None:
            sync_task.cancel()
            with suppress(asyncio.CancelledError):
                await sync_task


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(market_router)
app.include_router(sync_router)
app.include_router(predictions_router)
app.include_router(portfolio_router)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "status": "ok",
        "message": "4M Gold AI backend is running.",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
