"""
Endpoint pour mettre à jour le statut des anomalies
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.consumption import ConsumptionReading

router = APIRouter()


class UpdateAnomalyStatusRequest(BaseModel):
    """Modèle pour la mise à jour du statut"""
    status: str  # pending, verified, ignored


@router.patch("/anomalies/{reading_id}/status")
def update_anomaly_status(
    reading_id: int,
    status_update: UpdateAnomalyStatusRequest,
    db: Session = Depends(get_db)
):
    """
    Met à jour le statut d'une anomalie.
    
    **Statuts possibles:**
    - `pending` : En attente de vérification
    - `verified` : Anomalie confirmée
    - `ignored` : Fausse alerte, ignorée
    """
    # Vérifier le statut
    valid_statuses = ["pending", "verified", "ignored"]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Statut invalide. Utilisez : {', '.join(valid_statuses)}"
        )
    
    # Trouver la lecture
    reading = db.query(ConsumptionReading).filter(
        ConsumptionReading.id == reading_id
    ).first()
    
    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lecture {reading_id} introuvable"
        )
    
    if not reading.is_anomaly:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette lecture n'est pas marquée comme anomalie"
        )
    
    # Mettre à jour le statut
    reading.anomaly_status = status_update.status
    db.commit()
    db.refresh(reading)
    
    return {
        "reading_id": reading.id,
        "meter_id": reading.meter_id,
        "previous_status": "pending",  # Pourrait être tracké
        "new_status": reading.anomaly_status,
        "message": f"Statut mis à jour : {status_update.status}"
    }