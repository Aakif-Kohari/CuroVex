import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    POSTGRES_USER: str = "curovex"
    POSTGRES_PASSWORD: str = "curovex_postgres_dev"
    POSTGRES_DB: str = "curovex"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str | None = None
    
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "curovex_secret_key_dev")
    CORS_ORIGINS: str = "http://localhost:3000"
    
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "curovex_neo4j_dev"
    
    MODEL_PATH: str = "ml-core/artifacts/gat_link_predictor.pt"
    DATA_DIR: str = "kg-pipeline/data/normalized"
    
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 1440
    
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    @property
    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

config = Settings()
