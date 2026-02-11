"""
Schémas Pydantic pour l'entité Site
Ces schémas valident et sérialisent les données de l'API
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator

from app.models.site import SiteType


class SiteBase(BaseModel):
    """Schéma de base partagé entre création et mise à jour"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Nom du site énergétique",
        example="Parc Solaire Bordeaux"
    )
    site_type: SiteType = Field(
        ...,
        description="Type de site énergétique",
        example="solar"
    )
    location: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Localisation géographique",
        example="Bordeaux, France"
    )
    latitude: Optional[float] = Field(
        None,
        ge=-90,
        le=90,
        description="Latitude GPS",
        example=44.8378
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="Longitude GPS",
        example=-0.5792
    )
    capacity_kw: float = Field(
        ...,
        gt=0,
        description="Capacité en kilowatts",
        example=5000.0
    )
    description: Optional[str] = Field(
        None,
        description="Description détaillée du site",
        example="Installation de 150 panneaux solaires"
    )
    
    @validator('capacity_kw')
    def validate_capacity(cls, v):
        """Valide que la capacité est positive"""
        if v <= 0:
            raise ValueError('La capacité doit être supérieure à 0')
        return v


class SiteCreate(SiteBase):
    """
    Schéma pour la création d'un site.
    Utilisé dans POST /api/v1/sites
    
    Exemple de requête:
    {
        "name": "Parc Solaire Bordeaux",
        "site_type": "solar",
        "location": "Bordeaux, France",
        "latitude": 44.8378,
        "longitude": -0.5792,
        "capacity_kw": 5000.0,
        "description": "150 panneaux solaires"
    }
    """
    pass


class SiteUpdate(BaseModel):
    """
    Schéma pour la mise à jour d'un site.
    Tous les champs sont optionnels (mise à jour partielle)
    
    Utilisé dans PUT/PATCH /api/v1/sites/{id}
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    site_type: Optional[SiteType] = None
    location: Optional[str] = Field(None, min_length=1, max_length=255)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    capacity_kw: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None


class SiteResponse(SiteBase):
    """
    Schéma pour les réponses de l'API.
    Inclut les champs générés automatiquement (id, timestamps)
    
    Utilisé dans GET /api/v1/sites et GET /api/v1/sites/{id}
    
    Exemple de réponse:
    {
        "id": 1,
        "name": "Parc Solaire Bordeaux",
        "site_type": "solar",
        "location": "Bordeaux, France",
        "latitude": 44.8378,
        "longitude": -0.5792,
        "capacity_kw": 5000.0,
        "description": "150 panneaux solaires",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    }
    """
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        # Permet de créer le schéma depuis un modèle SQLAlchemy
        from_attributes = True


class SiteListResponse(BaseModel):
    """
    Schéma pour une liste paginée de sites
    """
    total: int = Field(..., description="Nombre total de sites")
    items: list[SiteResponse] = Field(..., description="Liste des sites")
    page: int = Field(..., description="Page actuelle")
    page_size: int = Field(..., description="Nombre d'items par page")