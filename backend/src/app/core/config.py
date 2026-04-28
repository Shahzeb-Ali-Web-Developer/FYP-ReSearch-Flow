import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    # LLM configuration
    # Prefer OpenAI if OPENAI_API_KEY is set, otherwise fall back to OpenRouter
    OPENAI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    CORE_API_KEY: Optional[str] = None
    SERPAPI_API_KEY: Optional[str] = None
    # Pinecone (used by chat_service RAG pipeline)
    PINECONE_API_KEY: Optional[str] = None
    
    # Neo4j Configuration
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    # CORS Configuration
    CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=[str(BASE_DIR / ".env"), str(BASE_DIR.parent / ".env")],
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()

# Export API keys to os.environ so that third-party libraries (LangChain,
# Pinecone SDK, etc.) that read keys via os.getenv() can find them.
_EXPORT_KEYS = [
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "PINECONE_API_KEY",
    "CORE_API_KEY",
    "SERPAPI_API_KEY",
]
for _key in _EXPORT_KEYS:
    _val = getattr(settings, _key, None)
    if _val and not os.getenv(_key):
        os.environ[_key] = _val