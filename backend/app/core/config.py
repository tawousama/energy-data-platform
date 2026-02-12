"""
Application Configuration using Pydantic Settings
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """
    Configuration centrale de l'application.
    Les valeurs sont chargées depuis les variables d'environnement ou le fichier .env
    """
    
    # Project Info
    PROJECT_NAME: str = "Energy Data Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # CORS - Origines autorisées
    BACKEND_CORS_ORIGINS: List[str] = [
        "https://frontend-production-443f.up.railway.app",
        "https://backend-production-7ef8.up.railway.app",
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    
    # Database PostgreSQL
    DATABASE_URL: str = "postgresql://energy_user:energy_password@localhost:5432/energy_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Anomaly Detection
    ANOMALY_DETECTION_THRESHOLD: float = 2.5  # Standard deviations
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instance globale des settings
settings = Settings()