"""
Consumption Reading Model - Mesures de consommation/production
"""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Index, Boolean, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ConsumptionReading(Base):
    """
    Table des lectures énergétiques.
    
    Stocke chaque mesure de production ou consommation d'un compteur.
    Volume important de données : partitionnement recommandé en production.
    
    Exemple de données:
        - 2024-01-15 10:00:00 | Compteur ABC | 125.5 kWh | Normal
        - 2024-01-15 10:15:00 | Compteur ABC | 320.0 kWh | Anomalie détectée!
    """
    __tablename__ = "consumption_readings"
    
    # Colonnes
    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(
        Integer,
        ForeignKey("meters.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Moment de la mesure"
    )
    value_kwh = Column(
        Float,
        nullable=False,
        comment="Valeur mesurée en kilowatt-heures"
    )
    
    # Détection d'anomalies
    is_anomaly = Column(
        Boolean,
        default=False,
        index=True,
        comment="True si cette mesure est une anomalie détectée"
    )
    anomaly_score = Column(
        Float,
        nullable=True,
        comment="Score de l'anomalie (ex: écart en sigmas)"
    )
    anomaly_status = Column(
        String(20),
        default="pending",
        index=True,
        comment="Statut: pending, verified, ignored"
    )
    
    # Timestamp de création
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relations
    meter = relationship("Meter", back_populates="readings")
    
    # Index composite pour les requêtes fréquentes
    # Optimise les requêtes du type: "Toutes les mesures du compteur X entre date1 et date2"
    __table_args__ = (
        Index('ix_meter_timestamp', 'meter_id', 'timestamp'),
    )
    
    def __repr__(self):
        anomaly_flag = " [ANOMALY]" if self.is_anomaly else ""
        return f"<Reading(id={self.id}, meter={self.meter_id}, value={self.value_kwh} kWh{anomaly_flag})>"
    
    def to_dict(self):
        """Convertit le modèle en dictionnaire"""
        return {
            "id": self.id,
            "meter_id": self.meter_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "value_kwh": self.value_kwh,
            "is_anomaly": self.is_anomaly,
            "anomaly_score": self.anomaly_score,
            "anomaly_status": self.anomaly_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }