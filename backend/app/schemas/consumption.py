"""
Schémas Pydantic pour les lectures de consommation
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ConsumptionReadingBase(BaseModel):
    """Schéma de base pour une lecture énergétique"""
    meter_id: int = Field(..., description="ID du compteur", example=1)
    timestamp: datetime = Field(
        ...,
        description="Moment de la mesure",
        example="2024-01-15T10:30:00Z"
    )
    value_kwh: float = Field(
        ...,
        ge=0,
        description="Valeur mesurée en kWh",
        example=125.5
    )
    
    @validator('value_kwh')
    def validate_value(cls, v):
        """Valide que la valeur est positive"""
        if v < 0:
            raise ValueError('La valeur doit être positive ou nulle')
        return v


class ConsumptionReadingCreate(ConsumptionReadingBase):
    """
    Schéma pour créer une nouvelle lecture.
    
    POST /api/v1/consumption/readings
    
    Exemple:
    {
        "meter_id": 1,
        "timestamp": "2024-01-15T10:30:00Z",
        "value_kwh": 125.5
    }
    """
    pass


class ConsumptionReadingResponse(ConsumptionReadingBase):
    """
    Schéma pour les réponses API incluant les anomalies.
    
    Exemple de réponse:
    {
        "id": 123,
        "meter_id": 1,
        "timestamp": "2024-01-15T10:30:00Z",
        "value_kwh": 125.5,
        "is_anomaly": false,
        "anomaly_score": null,
        "created_at": "2024-01-15T10:31:00Z"
    }
    """
    id: int
    is_anomaly: bool
    anomaly_score: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AggregatedConsumption(BaseModel):
    """
    Schéma pour les données agrégées (horaire, journalier, mensuel)
    
    Exemple:
    {
        "period": "2024-01-15",
        "total_kwh": 3000.0,
        "average_kwh": 125.0,
        "min_kwh": 80.0,
        "max_kwh": 180.0,
        "reading_count": 24
    }
    """
    period: str = Field(..., description="Période (date ou heure)")
    total_kwh: float = Field(..., description="Total de la période en kWh")
    average_kwh: float = Field(..., description="Moyenne de la période")
    min_kwh: Optional[float] = Field(None, description="Valeur minimale")
    max_kwh: Optional[float] = Field(None, description="Valeur maximale")
    reading_count: int = Field(..., description="Nombre de mesures")


class ConsumptionStats(BaseModel):
    """
    Statistiques de consommation pour un compteur
    
    Exemple:
    {
        "meter_id": 1,
        "period_days": 7,
        "total_kwh": 21000.0,
        "daily_average_kwh": 3000.0,
        "peak_kwh": 180.0,
        "anomaly_count": 3
    }
    """
    meter_id: int
    period_days: int
    total_kwh: float
    daily_average_kwh: float
    peak_kwh: float
    anomaly_count: int