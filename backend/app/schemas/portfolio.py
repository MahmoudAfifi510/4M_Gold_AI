from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class BuyTransactionCreate(BaseModel):
    weight_oz: float = Field(gt=0)
    karat: int = Field(ge=1, le=24)
    price: float = Field(gt=0)
    transaction_date: date


class SellTransactionCreate(BaseModel):
    sell_weight_oz: float = Field(gt=0)
    price: float = Field(gt=0)
    transaction_date: date


class BuyTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    weight_oz: float
    remaining_weight_oz: float
    sold_weight_oz: float
    karat: int
    price: float
    transaction_date: date
    spot_price: float
    current_value: float
    unrealized_profit_loss: float


class SellTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    buy_transaction_id: int
    sell_weight_oz: float
    price: float
    profit_loss: float
    transaction_date: date
    buy_weight_oz: float | None = None
    buy_karat: int | None = None


class PortfolioSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_profit_loss: float
    total_realized_profit_loss: float
    total_unrealized_profit_loss: float
    buys: list[BuyTransactionRead]
    sales: list[SellTransactionRead]
