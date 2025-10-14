from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SERPAPI_KEY: str
    SEMANTIC_KEY: str

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()