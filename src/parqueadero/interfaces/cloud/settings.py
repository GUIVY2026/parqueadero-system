from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class CloudSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PARQUEADERO_CLOUD_", extra="ignore")

    postgres_dsn: str = "postgresql+asyncpg://parqueadero:parqueadero@localhost:5432/parqueadero"
    host: str = "0.0.0.0"
    port: int = 8080
