"""
API Endpoints pour les Lectures de Consommation Énergétique

Fonctionnalités :
- Récupérer les lectures avec filtres (date, compteur)
- Créer une nouvelle lecture
- Agrégations horaires/journalières/mensuelles
- Statistiques de consommation
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.consumption import ConsumptionReading
from app.models.meter import Meter
from app.schemas.consumption import (
    ConsumptionReadingCreate,
    ConsumptionReadingResponse,
    AggregatedConsumption,
    ConsumptionStats
)

router = APIRouter()


@router.get("/readings", response_model=List[ConsumptionReadingResponse])
def get_consumption_readings(
    meter_id: Optional[int] = Query(None, description="Filtrer par compteur"),
    start_date: Optional[datetime] = Query(None, description="Date de début"),
    end_date: Optional[datetime] = Query(None, description="Date de fin"),
    only_anomalies: bool = Query(False, description="Uniquement les anomalies"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Récupère les lectures de consommation avec filtres.
    
    **Exemples :**
    - GET /consumption/readings?meter_id=1 → Toutes les lectures du compteur 1
    - GET /consumption/readings?start_date=2024-01-01 → Depuis le 1er janvier
    - GET /consumption/readings?only_anomalies=true → Uniquement les anomalies
    
    **Pagination :** Par défaut 100 résultats max
    """
    query = db.query(ConsumptionReading)
    
    # Filtrer par compteur
    if meter_id:
        query = query.filter(ConsumptionReading.meter_id == meter_id)
    
    # Filtrer par date de début
    if start_date:
        query = query.filter(ConsumptionReading.timestamp >= start_date)
    
    # Filtrer par date de fin
    if end_date:
        query = query.filter(ConsumptionReading.timestamp <= end_date)
    
    # Filtrer uniquement les anomalies
    if only_anomalies:
        query = query.filter(ConsumptionReading.is_anomaly == True)
    
    # Trier par date décroissante (plus récent en premier)
    query = query.order_by(ConsumptionReading.timestamp.desc())
    
    # Pagination
    readings = query.offset(skip).limit(limit).all()
    
    return readings


@router.post("/readings", response_model=ConsumptionReadingResponse, status_code=status.HTTP_201_CREATED)
def create_consumption_reading(
    reading_data: ConsumptionReadingCreate,
    db: Session = Depends(get_db)
):
    """
    Crée une nouvelle lecture de consommation.
    
    **Body :**
    ```json
    {
        "meter_id": 1,
        "timestamp": "2024-01-15T10:30:00Z",
        "value_kwh": 125.5
    }
    ```
    
    **Validations :**
    - Le compteur doit exister
    - La valeur doit être >= 0
    - Le timestamp doit être valide
    
    **Note :** La détection d'anomalie n'est pas automatique à la création.
    Utilisez POST /analytics/anomalies/detect/{meter_id} pour analyser.
    """
    # Vérifier que le compteur existe
    meter = db.query(Meter).filter(Meter.id == reading_data.meter_id).first()
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compteur avec l'ID {reading_data.meter_id} introuvable"
        )
    
    # Créer la lecture
    reading = ConsumptionReading(**reading_data.dict())
    db.add(reading)
    db.commit()
    db.refresh(reading)
    
    return reading


@router.get("/aggregated/hourly", response_model=List[AggregatedConsumption])
def get_hourly_aggregation(
    meter_id: int = Query(..., description="ID du compteur"),
    days: int = Query(7, ge=1, le=90, description="Nombre de jours d'historique"),
    db: Session = Depends(get_db)
):
    """
    Agrégation horaire de la consommation.
    
    **Retourne :** Somme et moyenne par heure sur les N derniers jours.
    
    **Exemple de réponse :**
    ```json
    [
        {
            "period": "2024-01-15 10:00:00",
            "total_kwh": 3000.0,
            "average_kwh": 125.0,
            "min_kwh": 100.0,
            "max_kwh": 150.0,
            "reading_count": 24
        }
    ]
    ```
    
    **Utilité :** Visualiser les patterns de consommation horaire.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Requête SQL avec agrégation par heure
    results = db.query(
        func.date_trunc('hour', ConsumptionReading.timestamp).label('hour'),
        func.sum(ConsumptionReading.value_kwh).label('total'),
        func.avg(ConsumptionReading.value_kwh).label('average'),
        func.min(ConsumptionReading.value_kwh).label('minimum'),
        func.max(ConsumptionReading.value_kwh).label('maximum'),
        func.count(ConsumptionReading.id).label('count')
    ).filter(
        ConsumptionReading.meter_id == meter_id,
        ConsumptionReading.timestamp >= cutoff
    ).group_by('hour').order_by('hour').all()
    
    # Formater les résultats
    return [
        AggregatedConsumption(
            period=r.hour.isoformat(),
            total_kwh=float(r.total),
            average_kwh=float(r.average),
            min_kwh=float(r.minimum),
            max_kwh=float(r.maximum),
            reading_count=r.count
        )
        for r in results
    ]


@router.get("/aggregated/daily", response_model=List[AggregatedConsumption])
def get_daily_aggregation(
    meter_id: int = Query(..., description="ID du compteur"),
    days: int = Query(30, ge=1, le=365, description="Nombre de jours"),
    db: Session = Depends(get_db)
):
    """
    Agrégation journalière de la consommation.
    
    **Retourne :** Total par jour sur les N derniers jours.
    
    **Utilité :** 
    - Comparer la consommation jour par jour
    - Détecter les tendances hebdomadaires
    - Identifier les jours atypiques
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    results = db.query(
        func.date_trunc('day', ConsumptionReading.timestamp).label('day'),
        func.sum(ConsumptionReading.value_kwh).label('total'),
        func.avg(ConsumptionReading.value_kwh).label('average'),
        func.min(ConsumptionReading.value_kwh).label('minimum'),
        func.max(ConsumptionReading.value_kwh).label('maximum'),
        func.count(ConsumptionReading.id).label('count')
    ).filter(
        ConsumptionReading.meter_id == meter_id,
        ConsumptionReading.timestamp >= cutoff
    ).group_by('day').order_by('day').all()
    
    return [
        AggregatedConsumption(
            period=r.day.date().isoformat(),
            total_kwh=float(r.total),
            average_kwh=float(r.average),
            min_kwh=float(r.minimum),
            max_kwh=float(r.maximum),
            reading_count=r.count
        )
        for r in results
    ]


@router.get("/stats/{meter_id}", response_model=ConsumptionStats)
def get_consumption_stats(
    meter_id: int,
    days: int = Query(7, ge=1, le=365, description="Période d'analyse"),
    db: Session = Depends(get_db)
):
    """
    Statistiques globales de consommation pour un compteur.
    
    **Retourne :**
    - Consommation totale sur la période
    - Moyenne journalière
    - Pic de consommation
    - Nombre d'anomalies détectées
    
    **Exemple de réponse :**
    ```json
    {
        "meter_id": 1,
        "period_days": 7,
        "total_kwh": 21000.0,
        "daily_average_kwh": 3000.0,
        "peak_kwh": 180.0,
        "anomaly_count": 3
    }
    ```
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Statistiques globales
    stats = db.query(
        func.sum(ConsumptionReading.value_kwh).label('total'),
        func.avg(ConsumptionReading.value_kwh).label('average'),
        func.max(ConsumptionReading.value_kwh).label('peak'),
        func.count(ConsumptionReading.id).label('count')
    ).filter(
        ConsumptionReading.meter_id == meter_id,
        ConsumptionReading.timestamp >= cutoff
    ).first()
    
    # Compter les anomalies
    anomaly_count = db.query(ConsumptionReading).filter(
        ConsumptionReading.meter_id == meter_id,
        ConsumptionReading.timestamp >= cutoff,
        ConsumptionReading.is_anomaly == True
    ).count()
    
    # Calculer la moyenne journalière
    total_kwh = float(stats.total) if stats.total else 0
    daily_avg = total_kwh / days if days > 0 else 0
    
    return ConsumptionStats(
        meter_id=meter_id,
        period_days=days,
        total_kwh=total_kwh,
        daily_average_kwh=daily_avg,
        peak_kwh=float(stats.peak) if stats.peak else 0,
        anomaly_count=anomaly_count
    )