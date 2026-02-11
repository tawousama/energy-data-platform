"""
API Endpoints pour l'Analyse et la Détection d'Anomalies

Fonctionnalités :
- Déclencher la détection d'anomalies
- Obtenir un résumé des anomalies
- Récupérer les anomalies détectées
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.anomaly_detection import AnomalyDetectionService
from app.models.meter import Meter

router = APIRouter()


@router.post("/anomalies/detect/{meter_id}")
def detect_anomalies(
    meter_id: int,
    method: str = Query(
        "zscore",
        description="Méthode de détection",
        regex="^(zscore|iqr|moving_average)$"
    ),
    db: Session = Depends(get_db)
):
    """
    Déclenche la détection d'anomalies pour un compteur.
    
    **Méthodes disponibles :**
    
    1. **zscore** (par défaut) :
       - Basée sur l'écart-type
       - Rapide et efficace
       - Recommandée pour données normalement distribuées
    
    2. **iqr** :
       - Basée sur les quartiles
       - Plus robuste aux outliers
       - Recommandée si données avec extrêmes
    
    3. **moving_average** :
       - Basée sur la moyenne mobile
       - Détecte les changements de pattern
       - Recommandée pour données avec tendances
    
    **Exemple :**
    ```
    POST /analytics/anomalies/detect/1?method=zscore
    ```
    
    **Réponse :**
    ```json
    {
        "meter_id": 1,
        "method": "zscore",
        "anomalies_detected": 5,
        "message": "5 anomalies détectées et marquées"
    }
    ```
    
    **Note :** Cette opération met à jour la base de données en marquant
    les lectures anormales (is_anomaly=True).
    """
    # Vérifier que le compteur existe
    meter = db.query(Meter).filter(Meter.id == meter_id).first()
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compteur avec l'ID {meter_id} introuvable"
        )
    
    # Créer le service de détection
    service = AnomalyDetectionService(db)
    
    try:
        # Lancer la détection
        count = service.mark_anomalies(meter_id, method=method)
        
        return {
            "meter_id": meter_id,
            "method": method,
            "anomalies_detected": count,
            "message": f"{count} anomalies détectées et marquées"
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/anomalies/summary/{meter_id}")
def get_anomaly_summary(
    meter_id: int,
    days: int = Query(7, ge=1, le=365, description="Période d'analyse en jours"),
    db: Session = Depends(get_db)
):
    """
    Récupère un résumé des anomalies pour un compteur.
    
    **Retourne :**
    - Nombre total de lectures sur la période
    - Nombre d'anomalies détectées
    - Taux d'anomalies (%)
    
    **Exemple de réponse :**
    ```json
    {
        "meter_id": 1,
        "period_days": 7,
        "total_readings": 672,
        "anomaly_count": 8,
        "anomaly_rate": 0.0119
    }
    ```
    
    **Interprétation :**
    - anomaly_rate < 0.01 (1%) : Excellent, système stable
    - 0.01 < anomaly_rate < 0.05 : Normal, surveillance recommandée
    - anomaly_rate > 0.05 (5%) : Attention ! Problème potentiel
    """
    # Vérifier que le compteur existe
    meter = db.query(Meter).filter(Meter.id == meter_id).first()
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compteur avec l'ID {meter_id} introuvable"
        )
    
    # Obtenir le résumé
    service = AnomalyDetectionService(db)
    summary = service.get_anomaly_summary(meter_id, days)
    
    return summary


@router.get("/anomalies/recent")
def get_recent_anomalies(
    hours: int = Query(24, ge=1, le=168, description="Dernières N heures"),
    limit: int = Query(50, ge=1, le=500, description="Nombre max de résultats"),
    db: Session = Depends(get_db)
):
    """
    Récupère les anomalies récentes de tous les compteurs.
    
    **Utilité :** Dashboard de surveillance en temps réel
    
    **Exemple :**
    ```
    GET /analytics/anomalies/recent?hours=24&limit=10
    ```
    
    **Réponse :**
    ```json
    [
        {
            "reading_id": 12345,
            "meter_id": 1,
            "timestamp": "2024-01-15T14:30:00Z",
            "value_kwh": 320.5,
            "anomaly_score": 4.2,
            "expected_range": "100-150 kWh"
        }
    ]
    ```
    """
    from datetime import datetime, timedelta
    from app.models.consumption import ConsumptionReading
    
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Récupérer les anomalies récentes
    anomalies = db.query(ConsumptionReading).filter(
        ConsumptionReading.is_anomaly == True,
        ConsumptionReading.timestamp >= cutoff
    ).order_by(
        ConsumptionReading.timestamp.desc()
    ).limit(limit).all()
    
    # Formater les résultats
    results = []
    for reading in anomalies:
        results.append({
            "reading_id": reading.id,
            "meter_id": reading.meter_id,
            "timestamp": reading.timestamp.isoformat(),
            "value_kwh": reading.value_kwh,
            "anomaly_score": reading.anomaly_score,
            "severity": (
                "critique" if reading.anomaly_score > 4 
                else "élevée" if reading.anomaly_score > 3 
                else "modérée"
            )
        })
    
    return {
        "period_hours": hours,
        "total_anomalies": len(results),
        "anomalies": results
    }


@router.delete("/anomalies/reset/{meter_id}", status_code=status.HTTP_204_NO_CONTENT)
def reset_anomalies(
    meter_id: int,
    db: Session = Depends(get_db)
):
    """
    Réinitialise les flags d'anomalies pour un compteur.
    
    **Utilité :** Après correction d'un problème, on peut nettoyer
    les anciennes anomalies pour repartir sur une base saine.
    
    ⚠️ **Attention :** Cette action ne supprime pas les données,
    elle remet juste is_anomaly=False pour toutes les lectures.
    """
    from app.models.consumption import ConsumptionReading
    
    # Vérifier que le compteur existe
    meter = db.query(Meter).filter(Meter.id == meter_id).first()
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compteur avec l'ID {meter_id} introuvable"
        )
    
    # Réinitialiser les flags
    db.query(ConsumptionReading).filter(
        ConsumptionReading.meter_id == meter_id,
        ConsumptionReading.is_anomaly == True
    ).update({
        "is_anomaly": False,
        "anomaly_score": None
    })
    
    db.commit()
    
    return None