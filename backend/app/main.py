"""
Energy Data Platform - Application FastAPI Principale

Point d'entrée de l'API REST pour la gestion des données énergétiques.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application.
    
    Startup: Initialisation de la base de données, connexions, etc.
    Shutdown: Nettoyage des ressources
    """
    # === STARTUP ===
    logger.info("🚀 Démarrage de l'Energy Data Platform API...")
    logger.info(f"📊 Environnement: {settings.ENVIRONMENT}")
    logger.info(f"🐛 Mode Debug: {settings.DEBUG}")
    
    # En production, utilisez Alembic pour les migrations
    # En dev, on peut créer les tables directement (à ne PAS faire en prod !)
    if settings.DEBUG:
        logger.info("🗄️  Création des tables (mode dev uniquement)...")
        Base.metadata.create_all(bind=engine)
    
    yield
    
    # === SHUTDOWN ===
    logger.info("🛑 Arrêt de l'Energy Data Platform API...")


# Créer l'application FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    API REST pour la gestion et l'analyse de données énergétiques en temps réel.
    
    ## Fonctionnalités
    
    * **Sites** : Gestion des sites de production/consommation énergétique
    * **Consumption** : Lectures et agrégations de consommation
    * **Analytics** : Détection d'anomalies avec 3 algorithmes (Z-score, IQR, Moving Average)
    
    ## Secteurs d'Application
    
    - Parcs solaires et éoliens
    - Centrales hydroélectriques
    - Sites industriels
    - Bâtiments intelligents
    """,
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,  # Swagger UI uniquement en dev
    redoc_url="/redoc" if settings.DEBUG else None,  # ReDoc uniquement en dev
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)


# === MIDDLEWARE ===

# CORS - Autoriser les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compression GZIP des réponses (améliore les performances réseau)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Middleware pour mesurer le temps de réponse
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Ajoute un header X-Process-Time à toutes les réponses.
    Utile pour le monitoring et le debugging.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Ajouter le header avec le temps en millisecondes
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    
    # Logger les requêtes lentes (> 1 seconde)
    if process_time > 1.0:
        logger.warning(
            f"⚠️  Requête lente: {request.method} {request.url.path} "
            f"a pris {process_time:.2f}s"
        )
    
    return response


# === GESTION D'ERREURS ===

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Gestionnaire global d'exceptions.
    Attrape toutes les erreurs non gérées pour éviter les crashes.
    """
    logger.error(f"❌ Erreur non gérée: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Erreur interne du serveur",
            "error": str(exc) if settings.DEBUG else "Une erreur s'est produite"
        }
    )


# === ENDPOINTS ===

@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint racine - Informations sur l'API
    """
    return {
        "message": "Energy Data Platform API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "documentation": f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
        "health": "/health",
        "api": settings.API_V1_STR
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check pour le monitoring.
    
    Utilisé par:
    - Docker health checks
    - Kubernetes liveness/readiness probes
    - Load balancers
    - Outils de monitoring (Prometheus, etc.)
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
        "timestamp": time.time()
    }


# Inclure tous les routers API
app.include_router(api_router, prefix=settings.API_V1_STR)


# === POINT D'ENTRÉE ===

if __name__ == "__main__":
    import uvicorn
    
    # Lancer le serveur en mode développement
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,  # Auto-reload en mode dev
        log_level="info"
    )