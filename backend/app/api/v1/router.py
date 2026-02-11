"""
Router Principal API v1

Regroupe tous les endpoints dans un seul router
qui sera inclus dans l'application FastAPI principale.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import sites, consumption, analytics, anomaly_status

# Créer le router principal
api_router = APIRouter()

# Inclure tous les sous-routers avec leurs préfixes et tags

# Sites énergétiques
api_router.include_router(
    sites.router,
    prefix="/sites",
    tags=["Sites"],
)

# Lectures de consommation
api_router.include_router(
    consumption.router,
    prefix="/consumption",
    tags=["Consumption"],
)

# Analytics et détection d'anomalies

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics"],
)

# Gestion des statuts d'anomalies
api_router.include_router(
    anomaly_status.router,
    prefix="/analytics",
    tags=["Analytics"],
)