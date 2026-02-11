"""
Meter Model - Représente un compteur/capteur d'énergie
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Meter(Base):
    """
    Table des compteurs énergétiques.
    
    Chaque site possède un ou plusieurs compteurs qui mesurent
    la production ou consommation d'énergie.
    
    Exemple:
        - Compteur "SOLAR_BDX_001" sur le site "Parc Solaire Bordeaux"
        - Type: "production", enregistre la production en kWh
    """
    __tablename__ = "meters"
    
    # Colonnes
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(
        Integer,
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    meter_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Identifiant physique unique du compteur"
    )
    meter_type = Column(
        String(50),
        nullable=False,
        comment="Type: 'production' ou 'consumption'"
    )
    is_active = Column(
        Boolean,
        default=True,
        comment="Indique si le compteur est actuellement actif"
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    site = relationship("Site", back_populates="meters")
    readings = relationship(
        "ConsumptionReading",
        back_populates="meter",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Meter(id={self.id}, meter_id='{self.meter_id}', type='{self.meter_type}')>"
    
    def to_dict(self):
        """Convertit le modèle en dictionnaire"""
        return {
            "id": self.id,
            "site_id": self.site_id,
            "meter_id": self.meter_id,
            "meter_type": self.meter_type,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }