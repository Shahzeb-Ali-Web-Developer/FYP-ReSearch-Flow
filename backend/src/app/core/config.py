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
    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = None
    PINECONE_API_KEY: Optional[str] = None
    
    # Pinecone RAG Configuration
    PINECONE_INDEX_NAME: str = "research-papers"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Upstash Redis Configuration
    UPSTASH_REDIS_REST_URL: Optional[str] = None
    UPSTASH_REDIS_REST_TOKEN: Optional[str] = None
    REDIS_CHAT_TTL: int = 3600  # 1 hour TTL for chat sessions

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