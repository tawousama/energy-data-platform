"""
Service de Détection d'Anomalies dans les Données Énergétiques

Implémente 3 algorithmes :
1. Z-Score : Détection basée sur l'écart-type
2. IQR : Détection basée sur les quartiles (robuste aux outliers)
3. Moving Average : Détection basée sur la moyenne mobile
"""
from typing import List, Tuple
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.consumption import ConsumptionReading
from app.core.config import settings


class AnomalyDetectionService:
    """Service pour détecter les anomalies dans les données énergétiques"""
    
    def __init__(self, db: Session):
        self.db = db
        self.threshold = settings.ANOMALY_DETECTION_THRESHOLD  # 2.5 sigma par défaut
    
    def detect_anomalies_zscore(
        self,
        meter_id: int,
        lookback_days: int = 30
    ) -> List[Tuple[int, float]]:
        """
        Détection d'anomalies par Z-Score.
        
        Principe: Une valeur est anormale si elle s'écarte de plus de 2.5 écarts-types
        de la moyenne.
        
        Exemple:
            Moyenne = 120 kWh, Écart-type = 10 kWh
            Valeur normale : 100-140 kWh
            Valeur anormale : < 95 kWh ou > 145 kWh (> 2.5 sigma)
        
        Args:
            meter_id: ID du compteur à analyser
            lookback_days: Nombre de jours historiques à analyser
            
        Returns:
            Liste de tuples (reading_id, anomaly_score)
        """
        # Récupérer les lectures historiques
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        readings = self.db.query(ConsumptionReading).filter(
            ConsumptionReading.meter_id == meter_id,
            ConsumptionReading.timestamp >= cutoff_date
        ).all()
        
        # Besoin d'au moins 10 valeurs pour être significatif
        if len(readings) < 10:
            return []
        
        # Extraire les valeurs en array NumPy
        values = np.array([r.value_kwh for r in readings])
        
        # Calculer moyenne et écart-type
        mean = np.mean(values)
        std = np.std(values)
        
        # Si écart-type = 0, toutes les valeurs sont identiques, pas d'anomalie
        if std == 0:
            return []
        
        # Calculer les Z-scores (nombre d'écarts-types depuis la moyenne)
        z_scores = np.abs((values - mean) / std)
        
        # Trouver les anomalies (Z-score > threshold)
        anomalies = []
        for reading, z_score in zip(readings, z_scores):
            if z_score > self.threshold:
                anomalies.append((reading.id, float(z_score)))
        
        return anomalies
    
    def detect_anomalies_iqr(
        self,
        meter_id: int,
        lookback_days: int = 30
    ) -> List[Tuple[int, float]]:
        """
        Détection d'anomalies par IQR (Interquartile Range).
        
        Principe: Méthode robuste basée sur les quartiles.
        Une valeur est anormale si elle est en dehors de [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
        
        Avantage: Moins sensible aux outliers extrêmes que le Z-Score
        
        Exemple:
            Q1 = 100 kWh, Q3 = 140 kWh, IQR = 40
            Bornes : [100 - 60, 140 + 60] = [40, 200]
            Anomalie si < 40 kWh ou > 200 kWh
        
        Args:
            meter_id: ID du compteur
            lookback_days: Nombre de jours d'historique
            
        Returns:
            Liste de tuples (reading_id, anomaly_score)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        readings = self.db.query(ConsumptionReading).filter(
            ConsumptionReading.meter_id == meter_id,
            ConsumptionReading.timestamp >= cutoff_date
        ).all()
        
        if len(readings) < 10:
            return []
        
        values = np.array([r.value_kwh for r in readings])
        
        # Calculer les quartiles
        q1 = np.percentile(values, 25)  # Premier quartile (25%)
        q3 = np.percentile(values, 75)  # Troisième quartile (75%)
        iqr = q3 - q1                    # Écart interquartile
        
        # Définir les bornes
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        
        # Trouver les anomalies
        anomalies = []
        for reading in readings:
            value = reading.value_kwh
            
            # Vérifier si hors des bornes
            if value < lower_bound or value > upper_bound:
                # Calculer un score basé sur la distance aux bornes
                if value < lower_bound:
                    score = (lower_bound - value) / iqr if iqr > 0 else 0
                else:
                    score = (value - upper_bound) / iqr if iqr > 0 else 0
                
                anomalies.append((reading.id, float(score)))
        
        return anomalies
    
    def detect_anomalies_moving_average(
        self,
        meter_id: int,
        window_hours: int = 24,
        threshold_multiplier: float = 2.0
    ) -> List[Tuple[int, float]]:
        """
        Détection d'anomalies par Moyenne Mobile.
        
        Principe: Compare chaque valeur à la moyenne des N valeurs précédentes.
        Utile pour détecter des changements soudains de pattern.
        
        Exemple:
            Moyenne mobile sur 24h = 120 kWh
            Nouvelle valeur = 250 kWh
            Écart = 130 kWh > 2 × std → ANOMALIE
        
        Args:
            meter_id: ID du compteur
            window_hours: Taille de la fenêtre de moyenne mobile
            threshold_multiplier: Multiplicateur du seuil (2.0 par défaut)
            
        Returns:
            Liste de tuples (reading_id, anomaly_score)
        """
        # Récupérer les lectures récentes (2x la fenêtre pour avoir assez de données)
        cutoff_date = datetime.utcnow() - timedelta(hours=window_hours * 2)
        readings = self.db.query(ConsumptionReading).filter(
            ConsumptionReading.meter_id == meter_id,
            ConsumptionReading.timestamp >= cutoff_date
        ).order_by(ConsumptionReading.timestamp).all()
        
        if len(readings) < window_hours:
            return []
        
        values = np.array([r.value_kwh for r in readings])
        
        # Calculer la moyenne mobile
        moving_avg = np.convolve(
            values,
            np.ones(window_hours) / window_hours,
            mode='valid'
        )
        
        # Calculer l'écart-type mobile
        moving_std = np.array([
            np.std(values[max(0, i - window_hours):i + 1])
            for i in range(len(values))
        ])
        
        # Détecter les anomalies
        anomalies = []
        for i, reading in enumerate(readings[window_hours - 1:], start=window_hours - 1):
            expected = moving_avg[i - window_hours + 1]
            deviation = abs(reading.value_kwh - expected)
            threshold = threshold_multiplier * moving_std[i]
            
            if deviation > threshold and moving_std[i] > 0:
                score = deviation / moving_std[i]
                anomalies.append((reading.id, float(score)))
        
        return anomalies
    
    def mark_anomalies(
        self,
        meter_id: int,
        method: str = "zscore"
    ) -> int:
        """
        Détecte et marque les anomalies dans la base de données.
        
        Cette fonction :
        1. Détecte les anomalies avec la méthode choisie
        2. Met à jour les enregistrements (is_anomaly=True, anomaly_score)
        3. Retourne le nombre d'anomalies trouvées
        
        Args:
            meter_id: ID du compteur à analyser
            method: Méthode de détection ('zscore', 'iqr', ou 'moving_average')
            
        Returns:
            Nombre d'anomalies détectées et marquées
            
        Raises:
            ValueError: Si la méthode est invalide
        """
        # Sélectionner la méthode de détection
        if method == "zscore":
            anomalies = self.detect_anomalies_zscore(meter_id)
        elif method == "iqr":
            anomalies = self.detect_anomalies_iqr(meter_id)
        elif method == "moving_average":
            anomalies = self.detect_anomalies_moving_average(meter_id)
        else:
            raise ValueError(f"Méthode inconnue: {method}")
        
        # Mettre à jour les enregistrements dans la base
        for reading_id, score in anomalies:
            reading = self.db.query(ConsumptionReading).get(reading_id)
            if reading:
                reading.is_anomaly = True
                reading.anomaly_score = score
        
        self.db.commit()
        
        return len(anomalies)
    
    def get_anomaly_summary(self, meter_id: int, days: int = 7) -> dict:
        """
        Obtient un résumé des anomalies pour un compteur.
        
        Args:
            meter_id: ID du compteur
            days: Période d'analyse en jours
            
        Returns:
            Dictionnaire avec les statistiques d'anomalies
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Compter toutes les lectures
        total_readings = self.db.query(ConsumptionReading).filter(
            ConsumptionReading.meter_id == meter_id,
            ConsumptionReading.timestamp >= cutoff_date
        ).count()
        
        # Compter les anomalies
        anomaly_count = self.db.query(ConsumptionReading).filter(
            ConsumptionReading.meter_id == meter_id,
            ConsumptionReading.timestamp >= cutoff_date,
            ConsumptionReading.is_anomaly == True
        ).count()
        
        return {
            "meter_id": meter_id,
            "period_days": days,
            "total_readings": total_readings,
            "anomaly_count": anomaly_count,
            "anomaly_rate": anomaly_count / total_readings if total_readings > 0 else 0
        }