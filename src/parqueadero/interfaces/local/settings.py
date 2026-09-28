from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class LocalSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PARQUEADERO_LOCAL_", extra="ignore")

    sqlite_path: str = "data/local.sqlite3"
    host: str = "127.0.0.1"
    port: int = 8000
    node_id: str = "nodo-local"
