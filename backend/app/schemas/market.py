from datetime import date
from pydantic import BaseModel


class MarketDataRead(BaseModel):
    market_date: date
    gold_price: float
    oil_price: float
    usd_index: float
