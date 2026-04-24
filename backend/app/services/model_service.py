from __future__ import annotations

import math
import pickle
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LinearRegression
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.schema import HistoricalMarketData, Prediction


class ModelService:
    FEATURE_COLUMNS = ["prev1", "ma7", "ma30", "trend7"]

    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_path = Path(self.settings.model_file)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)

    def _build_feature_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        frame = df.copy().sort_values("market_date").reset_index(drop=True)
        frame["ma7"] = frame["price"].rolling(7).mean()
        frame["ma30"] = frame["price"].rolling(30).mean()
        frame["trend7"] = frame["price"] - frame["price"].shift(7)
        frame["prev1"] = frame["price"].shift(1)
        frame["target"] = frame["price"].shift(-1)
        frame.dropna(inplace=True)
        return frame

    def _history_to_frame(self, rows: list[HistoricalMarketData]) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "market_date": row.market_date,
                    "price": float(row.gold_price),
                }
                for row in rows
            ]
        )

    def train(self, session: Session) -> str:
        rows = session.execute(
            select(HistoricalMarketData).order_by(HistoricalMarketData.market_date.asc())
        ).scalars().all()
        if len(rows) < 40:
            raise RuntimeError("Not enough historical market data to train the model.")

        df = self._history_to_frame(rows)
        train_frame = self._build_feature_frame(df)
        if train_frame.empty:
            raise RuntimeError("Not enough cleaned training rows after feature preparation.")

        model = LinearRegression()
        model.fit(train_frame[self.FEATURE_COLUMNS].to_numpy(), train_frame["target"].to_numpy())

        with self.model_path.open("wb") as handle:
            pickle.dump(
                {
                    "model": model,
                    "feature_columns": self.FEATURE_COLUMNS,
                    "trained_at": datetime.utcnow().isoformat(),
                    "version": "linreg-gold-v3",
                },
                handle,
            )

        return str(self.model_path)

    def _load_artifact(self) -> dict:
        if not self.model_path.exists():
            raise RuntimeError("Model artifact not found. Train the model first.")
        with self.model_path.open("rb") as handle:
            artifact = pickle.load(handle)
        if isinstance(artifact, LinearRegression):
            artifact = {
                "model": artifact,
                "feature_columns": self.FEATURE_COLUMNS,
                "version": "linreg-gold-v1",
            }
        return artifact

    def _sigmoid(self, value: float) -> float:
        return 1.0 / (1.0 + math.exp(-value))

    def _latest_feature_row(self, df: pd.DataFrame) -> pd.Series:
        frame = self._build_feature_frame(df)
        if frame.empty:
            raise RuntimeError("Not enough data to create prediction features.")
        return frame.iloc[-1]

    def _append_future_row(self, df: pd.DataFrame, market_date: date, gold_price: float) -> pd.DataFrame:
        future_row = {
            "market_date": market_date,
            "price": float(gold_price),
        }
        return pd.concat([df, pd.DataFrame([future_row])], ignore_index=True)

    def predict_next_days(self, session: Session, days: int = 5) -> list[dict]:
        rows = session.execute(
            select(HistoricalMarketData).order_by(HistoricalMarketData.market_date.asc())
        ).scalars().all()
        if len(rows) < 40:
            raise RuntimeError("Not enough historical market data for predictions.")

        artifact = self._load_artifact()
        model = artifact["model"]
        feature_columns = artifact.get("feature_columns", self.FEATURE_COLUMNS)

        history = self._history_to_frame(rows).tail(180).reset_index(drop=True)
        base_date = datetime.now(self.settings.local_timezone).date()
        results = []
        recent_changes = history["price"].diff().dropna().tail(14)
        volatility = float(recent_changes.abs().mean()) if not recent_changes.empty else 1.0
        volatility = max(volatility, 0.75)

        for offset in range(1, days + 1):
            latest_features = self._latest_feature_row(history)
            X = latest_features[feature_columns].to_numpy(dtype=float).reshape(1, -1)
            predicted_price = float(model.predict(X)[0])
            current_price = float(history["price"].iloc[-1])
            delta = predicted_price - current_price
            confidence = self._sigmoid(delta / volatility)
            up_probability = round(confidence * 100.0, 3)
            down_probability = round(100.0 - up_probability, 3)
            direction = "UP" if up_probability >= 50.0 else "DOWN"
            prediction_date = base_date + timedelta(days=offset)

            results.append(
                {
                    "date": prediction_date.isoformat(),
                    "up_probability": up_probability,
                    "down_probability": down_probability,
                    "direction": direction,
                }
            )

            history = self._append_future_row(history, prediction_date, predicted_price)

        for item in results:
            prediction_date = date.fromisoformat(item["date"])
            existing = session.execute(
                select(Prediction).where(Prediction.prediction_date == prediction_date)
            ).scalar_one_or_none()
            if existing:
                existing.base_date = base_date
                existing.up_probability = item["up_probability"]
                existing.down_probability = item["down_probability"]
                existing.direction = item["direction"]
                existing.model_version = artifact.get("version", "linreg-gold-v3")
            else:
                session.add(
                    Prediction(
                        prediction_date=prediction_date,
                        base_date=base_date,
                        up_probability=item["up_probability"],
                        down_probability=item["down_probability"],
                        direction=item["direction"],
                        model_version=artifact.get("version", "linreg-gold-v3"),
                    )
                )
        session.commit()
        return results
