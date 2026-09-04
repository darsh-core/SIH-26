from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "SIH Competency Intelligence & Learning Platform"
    API_V1_STR: str = "/api/v1"
    
    # Default to macOS local Homebrew Postgres on port 5433 for passwordless access
    DATABASE_URL: str = "postgresql://darshini@localhost:5433/sih_platform"
    
    # Path to synthetic mock data
    MOCK_DATA_DIR: str = str(Path(__file__).resolve().parents[3] / "mock-data")
    
    # REDIS Config
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Security
    SECRET_KEY: str = "supersecretkeychangeinproduction"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # AI & Embeddings Config
    AI_PROVIDER: str = "ollama"  # "ollama", "groq", or "mock"
    EMBEDDING_PROVIDER: str = "sentence_transformer"  # "sentence_transformer" or "mock"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"
    OLLAMA_TIMEOUT: int = 120
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"  # or "openai/gpt-oss-20b", "qwen/qwen3.6-27b"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # Learning Provider Integration Config
    LEARNING_PROVIDER: str = "demo"  # "demo" or "igot"
    IGOT_API_BASE_URL: Optional[str] = None
    IGOT_CLIENT_ID: Optional[str] = None
    IGOT_CLIENT_SECRET: Optional[str] = None
    IGOT_TOKEN_URL: Optional[str] = None
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()
