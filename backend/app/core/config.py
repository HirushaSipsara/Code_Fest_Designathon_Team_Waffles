from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://livlink:livlink@localhost:5432/livlink"
    ai_provider: str = "gemini"  # "gemini" or "openai" — picks which AIProvider parse_scene_request() uses
    ai_api_key: str | None = None
    ai_model: str | None = None
    ai_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    ai_use_seeded: bool = True  # True = keyword-matching NL engine; False = call real LLM
    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 0
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

@lru_cache
def get_settings() -> Settings:
    return Settings()
