from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MedFlow AI API"
    app_env: str = "development"
    app_debug: bool = True
    app_version: str = "0.1.0"
    api_base_path: str = "/api/v1"
    database_url: str = "postgresql+psycopg://medflow:medflow_dev_password@db:5432/medflow"
    jwt_secret_key: str = "change-me-in-production"
    jwt_issuer: str = "medflow-ai"
    jwt_audience: str = "medflow-api"
    jwt_algorithm: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
