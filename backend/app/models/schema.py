from datetime import datetime, date

from sqlalchemy import CheckConstraint, Date, DateTime, DECIMAL, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    buy_transactions = relationship("GoldTransaction", back_populates="user", cascade="all, delete-orphan")
    sell_transactions = relationship("GoldSaleTransaction", back_populates="user", cascade="all, delete-orphan")


class HistoricalMarketData(Base):
    __tablename__ = "historical_market_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    market_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    gold_price: Mapped[float] = mapped_column(DECIMAL(18, 6), nullable=False)
    oil_price: Mapped[float] = mapped_column(DECIMAL(18, 6), nullable=False)
    usd_index: Mapped[float] = mapped_column(DECIMAL(18, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="alpha_vantage")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (Index("idx_market_date", "market_date"),)


class GoldTransaction(Base):
    __tablename__ = "gold_buy_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    weight_oz: Mapped[float] = mapped_column(DECIMAL(18, 4), nullable=False)
    remaining_weight_oz: Mapped[float] = mapped_column(DECIMAL(18, 4), nullable=False)
    karat: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(18, 6), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="buy_transactions")
    sales = relationship("GoldSaleTransaction", back_populates="buy_transaction", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("karat > 0 AND karat <= 24", name="ck_transactions_karat_range"),
    )


class GoldSaleTransaction(Base):
    __tablename__ = "gold_sale_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    buy_transaction_id: Mapped[int] = mapped_column(
        ForeignKey("gold_buy_transactions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sell_weight_oz: Mapped[float] = mapped_column(DECIMAL(18, 4), nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(18, 6), nullable=False)
    profit_loss: Mapped[float] = mapped_column(DECIMAL(18, 6), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="sell_transactions")
    buy_transaction = relationship("GoldTransaction", back_populates="sales")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    base_date: Mapped[date] = mapped_column(Date, nullable=False)
    up_probability: Mapped[float] = mapped_column(DECIMAL(6, 3), nullable=False)
    down_probability: Mapped[float] = mapped_column(DECIMAL(6, 3), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False, default="linreg-v2")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class MarketDataSyncLog(Base):
    __tablename__ = "market_data_sync_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sync_type: Mapped[str] = mapped_column(String(50), nullable=False)
    sync_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    market_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    api_calls_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
