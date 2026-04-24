from datetime import date
from pydantic import BaseModel


class PredictionRead(BaseModel):
    date: date
    up_probability: float
    down_probability: float
    direction: str


class PredictionResponse(BaseModel):
    generated_at: date
    predictions: list[PredictionRead]

