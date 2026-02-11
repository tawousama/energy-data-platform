"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

# Créer le moteur SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # Teste les connexions avant utilisation
    pool_size=10,            # 10 connexions dans le pool
    max_overflow=20,         # 20 connexions supplémentaires si besoin
    echo=settings.DEBUG      # Log des requêtes SQL en mode debug
)

# Créer la factory de sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Classe de base pour les modèles
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection pour obtenir une session de base de données.
    
    Usage dans FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    La session est automatiquement fermée après la requête.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()