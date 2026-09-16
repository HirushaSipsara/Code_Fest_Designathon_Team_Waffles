from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://livlink:livlink@localhost:5432/livlink"
    ai_api_key: str | None = None
    ai_model: str | None = None
    ai_base_url: str = "https://api.openai.com/v1"
    cors_origins: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
