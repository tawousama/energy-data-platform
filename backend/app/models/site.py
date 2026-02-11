"""
Site Model - Représente un site de production/consommation énergétique
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class SiteType(str, enum.Enum):
    """Types de sites énergétiques"""
    SOLAR = "solar"          # Parc solaire
    WIND = "wind"            # Parc éolien
    HYDRO = "hydro"          # Centrale hydroélectrique
    NUCLEAR = "nuclear"      # Centrale nucléaire
    THERMAL = "thermal"      # Centrale thermique
    CONSUMER = "consumer"    # Site consommateur


class Site(Base):
    """
    Table des sites énergétiques.
    
    Un site peut être un lieu de production (parc solaire, éolien, etc.)
    ou un lieu de consommation (usine, bâtiment).
    
    Exemple:
        - "Parc Solaire Bordeaux" : 150 panneaux, 5000 kW
        - "Éolienne Offshore Bretagne" : 50 turbines, 75000 kW
    """
    __tablename__ = "sites"
    
    # Colonnes
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True, unique=True)
    site_type = Column(SQLEnum(SiteType), nullable=False, index=True)
    location = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    capacity_kw = Column(Float, nullable=False)  # Capacité en kilowatts
    description = Column(Text, nullable=True)
    
    # Timestamps automatiques
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    meters = relationship(
        "Meter",
        back_populates="site",
        cascade="all, delete-orphan"  # Si on supprime le site, on supprime les compteurs
    )
    
    def __repr__(self):
        return f"<Site(id={self.id}, name='{self.name}', type='{self.site_type}')>"
    
    def to_dict(self):
        """Convertit le modèle en dictionnaire pour JSON"""
        return {
            "id": self.id,
            "name": self.name,
            "site_type": self.site_type.value,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "capacity_kw": self.capacity_kw,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }