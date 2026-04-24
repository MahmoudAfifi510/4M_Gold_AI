from __future__ import annotations

import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import get_settings


logger = logging.getLogger(__name__)


class AlphaVantageError(RuntimeError):
    pass


class AlphaVantageRateLimitError(AlphaVantageError):
    pass


@dataclass(frozen=True)
class MarketSeries:
    name: str
    frame: pd.DataFrame


class AlphaVantageService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1.0,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _request_json(self, params: dict[str, str]) -> dict[str, Any]:
        if not self.settings.alpha_vantage_api_key:
            raise RuntimeError("ALPHA_VANTAGE_API_KEY is missing.")
        query = {"apikey": self.settings.alpha_vantage_api_key, **params}
        response: Response = self.session.get(
            self.settings.alpha_vantage_base_url,
            params=query,
            timeout=45,
        )
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            note = payload.get("Note")
            info = payload.get("Information")
            error = payload.get("Error Message")
            if error:
                raise AlphaVantageError(str(error))
            if note:
                raise AlphaVantageRateLimitError(str(note))
            if info:
                raise AlphaVantageRateLimitError(str(info))
        return payload

    @staticmethod
    def _is_date_key(value: str) -> bool:
        return len(value) >= 8 and value[0:4].isdigit() and value[5:7].isdigit() and value[8:10].isdigit()

    @staticmethod
    def _parse_date(value: Any) -> pd.Timestamp | None:
        if value is None:
            return None
        try:
            parsed = pd.to_datetime(value, utc=False, errors="coerce")
        except Exception:
            return None
        if pd.isna(parsed):
            return None
        timestamp = pd.Timestamp(parsed)
        if timestamp.tzinfo is not None:
            timestamp = timestamp.tz_convert(None)
        return timestamp

    @staticmethod
    def _extract_numeric(value: Any) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(",", "").strip())
            except ValueError:
                return None
        return None

    def _value_from_row(self, row: Any) -> float | None:
        if isinstance(row, dict):
            preferred_keys = [
                "close",
                "4. close",
                "adjusted close",
                "5. adjusted close",
                "value",
                "price",
                "rate",
                "usd_index",
            ]
            lowered = {str(key).lower(): key for key in row.keys()}
            for key in preferred_keys:
                actual_key = lowered.get(key.lower())
                if actual_key is not None:
                    extracted = self._extract_numeric(row.get(actual_key))
                    if extracted is not None:
                        return extracted
            for item in row.values():
                extracted = self._extract_numeric(item)
                if extracted is not None:
                    return extracted
            return None
        return self._extract_numeric(row)

    def _parse_series(self, payload: dict[str, Any]) -> pd.DataFrame:
        if not isinstance(payload, dict):
            raise AlphaVantageError("Unexpected Alpha Vantage response format.")

        candidate = None
        for key, value in payload.items():
            if isinstance(value, dict) or isinstance(value, list):
                lower_key = str(key).lower()
                if any(
                    marker in lower_key
                    for marker in (
                        "time series",
                        "data",
                        "history",
                        "values",
                        "series",
                    )
                ):
                    candidate = value
                    break
        if candidate is None:
            # Fall back to the first structured payload if Alpha Vantage changes the wrapper key.
            for value in payload.values():
                if isinstance(value, (dict, list)):
                    candidate = value
                    break
        if candidate is None:
            keys = ", ".join(sorted(payload.keys()))
            raise AlphaVantageError(f"No market data series found in Alpha Vantage response. Keys: {keys}")

        rows: list[dict[str, Any]] = []
        if isinstance(candidate, dict):
            for raw_date, raw_row in candidate.items():
                parsed_date = self._parse_date(raw_date)
                parsed_value = self._value_from_row(raw_row)
                if parsed_date is not None and parsed_value is not None:
                    rows.append({"market_date": parsed_date.date(), "value": parsed_value})
        elif isinstance(candidate, list):
            for raw_row in candidate:
                parsed_date = None
                parsed_value = None
                if isinstance(raw_row, dict):
                    for date_key in ("date", "time", "timestamp"):
                        if date_key in raw_row:
                            parsed_date = self._parse_date(raw_row.get(date_key))
                            if parsed_date is not None:
                                break
                    parsed_value = self._value_from_row(raw_row)
                else:
                    parsed_value = self._extract_numeric(raw_row)
                if parsed_date is not None and parsed_value is not None:
                    rows.append({"market_date": parsed_date.date(), "value": parsed_value})

        frame = pd.DataFrame(rows)
        if frame.empty:
            keys = ", ".join(sorted(payload.keys()))
            raise AlphaVantageError(f"Alpha Vantage returned an empty market series. Keys: {keys}")
        frame = frame.dropna(subset=["market_date", "value"])
        frame = frame.sort_values("market_date").drop_duplicates("market_date", keep="last")
        return frame.reset_index(drop=True)

    def _fetch_series(self, params: dict[str, str], column_name: str) -> MarketSeries:
        payload = self._request_json(params)
        frame = self._parse_series(payload).rename(columns={"value": column_name})
        logger.info("Fetched %s market series with %s rows.", column_name, len(frame))
        return MarketSeries(name=column_name, frame=frame)

    def _latest_value_from_series(self, params: dict[str, str], column_name: str) -> float:
        payload = self._request_json(params)
        frame = self._parse_series(payload)
        latest = frame.iloc[-1]["value"]
        value = float(latest)
        logger.info("Fetched latest %s value.", column_name)
        return value

    def _current_market_date(self) -> pd.Timestamp:
        return pd.Timestamp(datetime.now(self.settings.local_timezone)).normalize()

    def fetch_gold_history(self) -> pd.DataFrame:
        return self._fetch_series(
            {"function": "GOLD_SILVER_HISTORY", "symbol": "GOLD", "interval": "daily"},
            "gold_price",
        ).frame

    def fetch_gold_latest(self) -> float:
        return self._latest_value_from_series(
            {"function": "GOLD_SILVER_SPOT", "symbol": "GOLD"},
            "gold_price",
        )

    def fetch_oil_history(self) -> pd.DataFrame:
        return self._fetch_series(
            {"function": "WTI", "interval": "daily"},
            "oil_price",
        ).frame

    def fetch_oil_latest(self) -> float:
        return self._latest_value_from_series(
            {"function": "WTI", "interval": "daily"},
            "oil_price",
        )

    def fetch_usd_index_history(self) -> pd.DataFrame:
        # Alpha Vantage does not expose the DXY ticker directly in the free docs,
        # so we store a USD strength proxy from the USD/EUR FX daily series.
        return self._fetch_series(
            {"function": "FX_DAILY", "from_symbol": "USD", "to_symbol": "EUR", "outputsize": "full"},
            "usd_index",
        ).frame

    def fetch_usd_index_latest(self) -> float:
        return self._latest_value_from_series(
            {"function": "FX_DAILY", "from_symbol": "USD", "to_symbol": "EUR"},
            "usd_index",
        )

    def fetch_daily_snapshot(self) -> pd.DataFrame:
        today = self._current_market_date().date()
        return pd.DataFrame(
            [
                {
                    "market_date": today,
                    "gold_price": self.fetch_gold_latest(),
                    "oil_price": self.fetch_oil_latest(),
                    "usd_index": self.fetch_usd_index_latest(),
                }
            ]
        )
