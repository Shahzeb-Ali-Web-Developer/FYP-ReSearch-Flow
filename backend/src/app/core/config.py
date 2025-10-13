from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SERPAPI_KEY: str
    SEMANTIC_KEY: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
