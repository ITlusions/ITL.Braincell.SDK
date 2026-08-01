import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://braincell:braincell_dev_password@braincell-itl-braincell-postgres:5432/braincell"
    )
    
    # Weaviate
    weaviate_url: str = os.getenv("WEAVIATE_URL", "http://weaviate:80")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379")
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = environment == "development"
    
    # API
    api_title: str = "BrainCell"
    api_version: str = "0.1.0"
    
    # Embedding model
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
