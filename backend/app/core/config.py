from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from zoneinfo import ZoneInfo

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="4M Gold AI", alias="APP_NAME")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=60 * 24, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    frontend_origins: str = Field(
        default="http://localhost:5173",
        validation_alias=AliasChoices("FRONTEND_ORIGINS", "FRONTEND_URL"),
    )
    app_timezone: str = Field(default="Africa/Cairo", alias="APP_TIMEZONE")

    gold_ticker: str = Field(default="GC=F", alias="GOLD_TICKER")
    oil_ticker: str = Field(default="CL=F", alias="OIL_TICKER")
    usd_ticker: str = Field(default="DX-Y.NYB", alias="USD_TICKER")
    model_path: str = Field(default="artifacts/gold_model.pkl", alias="MODEL_PATH")
    alpha_vantage_api_key: Optional[str] = Field(default=None, alias="ALPHA_VANTAGE_API_KEY")
    alpha_vantage_base_url: str = Field(default="https://www.alphavantage.co/query", alias="ALPHA_VANTAGE_BASE_URL")

    auto_sync_on_startup: bool = Field(default=True, alias="AUTO_SYNC_ON_STARTUP")
    auto_train_on_startup: bool = Field(default=True, alias="AUTO_TRAIN_ON_STARTUP")

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip().rstrip("/") for origin in self.frontend_origins.split(",") if origin.strip()]

    @property
    def resolved_database_url(self) -> str:
        if not self.database_url:
            raise RuntimeError("Missing DATABASE_URL. Set it to the Railway public MySQL URL.")
        return self.database_url

    @property
    def model_file(self) -> Path:
        return Path(self.model_path)

    @property
    def local_timezone(self) -> ZoneInfo:
        return ZoneInfo(self.app_timezone)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
