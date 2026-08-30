from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "SIH Competency Intelligence & Learning Platform"
    API_V1_STR: str = "/api/v1"
    
    # Default to macOS local Homebrew Postgres on port 5433 for passwordless access
    DATABASE_URL: str = "postgresql://darshini@localhost:5433/sih_platform"
    
    # Path to synthetic mock data
    MOCK_DATA_DIR: str = "/Users/darshini/.gemini/antigravity-ide/scratch/sih-competency-platform/mock-data"
    
    # REDIS Config
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Security
    SECRET_KEY: str = "supersecretkeychangeinproduction"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
