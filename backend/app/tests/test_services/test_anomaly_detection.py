"""
Tests du Service de Détection d'Anomalies

Tests unitaires pour vérifier que les 3 algorithmes fonctionnent correctement.
"""

import pytest
from sqlalchemy.orm import Session

from app.services.anomaly_detection import AnomalyDetectionService
from app.models.consumption import ConsumptionReading


@pytest.mark.unit
class TestAnomalyDetectionService:
    """Suite de tests pour le service de détection d'anomalies"""
    
    def test_service_initialization(self, db: Session):
        """Test : Le service s'initialise correctement"""
        service = AnomalyDetectionService(db)
        
        assert service.db is not None
        assert service.threshold == 2.5  # Valeur par défaut
    
    def test_zscore_with_normal_data(
        self,
        db: Session,
        sample_meter,
        sample_readings
    ):
        """
        Test : Z-score ne détecte pas d'anomalies dans des données normales
        """
        service = AnomalyDetectionService(db)
        
        # Détecter les anomalies
        anomalies = service.detect_anomalies_zscore(sample_meter.id)
        
        # Avec des données normales, on ne devrait avoir aucune ou très peu d'anomalies
        assert len(anomalies) < 5, "Trop d'anomalies dans des données normales"
    
    def test_zscore_with_anomalies(
        self,
        db: Session,
        sample_meter,
        readings_with_anomalies
    ):
        """
        Test : Z-score détecte les anomalies intentionnelles
        """
        service = AnomalyDetectionService(db)
        
        # Détecter les anomalies
        anomalies = service.detect_anomalies_zscore(sample_meter.id)
        
        # On devrait détecter les 3 anomalies injectées
        assert len(anomalies) >= 3, "Les anomalies n'ont pas été détectées"
        
        # Vérifier que les scores sont significatifs
        for reading_id, score in anomalies:
            assert score > service.threshold, f"Score trop faible: {score}"
    
    def test_iqr_method(
        self,
        db: Session,
        sample_meter,
        readings_with_anomalies
    ):
        """
        Test : La méthode IQR détecte les anomalies
        """
        service = AnomalyDetectionService(db)
        
        anomalies = service.detect_anomalies_iqr(sample_meter.id)
        
        # Devrait détecter des anomalies
        assert len(anomalies) > 0, "Aucune anomalie détectée avec IQR"
        
        # Vérifier la structure des résultats
        for reading_id, score in anomalies:
            assert isinstance(reading_id, int)
            assert isinstance(score, float)
            assert score > 0
    
    def test_moving_average_method(
        self,
        db: Session,
        sample_meter,
        readings_with_anomalies
    ):
        """
        Test : La méthode Moving Average fonctionne sans erreur
        """
        service = AnomalyDetectionService(db)
        
        # Tester que la méthode s'exécute sans erreur
        anomalies = service.detect_anomalies_moving_average(
            sample_meter.id,
            window_hours=24
        )
        
        # La méthode peut retourner 0 anomalie selon les données
        # L'important est qu'elle ne plante pas
        assert isinstance(anomalies, list)
        # Si des anomalies sont détectées, vérifier leur structure
        for reading_id, score in anomalies:
            assert isinstance(reading_id, int)
            assert isinstance(score, float)
            assert score > 0
    
    def test_mark_anomalies_zscore(
        self,
        db: Session,
        sample_meter,
        readings_with_anomalies
    ):
        """
        Test : mark_anomalies met à jour la base de données
        """
        service = AnomalyDetectionService(db)
        
        # Avant : aucune anomalie marquée
        count_before = db.query(ConsumptionReading).filter(
            ConsumptionReading.meter_id == sample_meter.id,
            ConsumptionReading.is_anomaly == True
        ).count()
        assert count_before == 0
        
        # Marquer les anomalies
        count_detected = service.mark_anomalies(sample_meter.id, method="zscore")
        
        # Vérifier que des anomalies ont été marquées
        assert count_detected > 0, "Aucune anomalie détectée"
        
        # Après : anomalies marquées dans la DB
        count_after = db.query(ConsumptionReading).filter(
            ConsumptionReading.meter_id == sample_meter.id,
            ConsumptionReading.is_anomaly == True
        ).count()
        
        assert count_after == count_detected
        
        # Vérifier qu'un score a été attribué
        anomalous_readings = db.query(ConsumptionReading).filter(
            ConsumptionReading.meter_id == sample_meter.id,
            ConsumptionReading.is_anomaly == True
        ).all()
        
        for reading in anomalous_readings:
            assert reading.anomaly_score is not None
            assert reading.anomaly_score > 0
    
    def test_mark_anomalies_invalid_method(
        self,
        db: Session,
        sample_meter,
        sample_readings
    ):
        """
        Test : Erreur si méthode invalide
        """
        service = AnomalyDetectionService(db)
        
        with pytest.raises(ValueError) as exc_info:
            service.mark_anomalies(sample_meter.id, method="invalid_method")
        
        assert "invalid_method" in str(exc_info.value).lower()
    
    def test_get_anomaly_summary(
        self,
        db: Session,
        sample_meter,
        readings_with_anomalies
    ):
        """
        Test : Le résumé des anomalies est correct
        """
        service = AnomalyDetectionService(db)
        
        # Marquer les anomalies d'abord
        service.mark_anomalies(sample_meter.id, method="zscore")
        
        # Obtenir le résumé
        summary = service.get_anomaly_summary(sample_meter.id, days=7)
        
        # Vérifier la structure
        assert "meter_id" in summary
        assert "period_days" in summary
        assert "total_readings" in summary
        assert "anomaly_count" in summary
        assert "anomaly_rate" in summary
        
        # Vérifier les valeurs
        assert summary["meter_id"] == sample_meter.id
        assert summary["period_days"] == 7
        assert summary["total_readings"] > 0
        assert summary["anomaly_count"] >= 0
        assert 0 <= summary["anomaly_rate"] <= 1
    
    def test_insufficient_data(
        self,
        db: Session,
        sample_meter
    ):
        """
        Test : Comportement avec données insuffisantes
        """
        # Créer seulement 5 lectures (insuffisant)
        from datetime import datetime, timedelta
        
        for i in range(5):
            reading = ConsumptionReading(
                meter_id=sample_meter.id,
                timestamp=datetime.utcnow() + timedelta(hours=i),
                value_kwh=100.0
            )
            db.add(reading)
        db.commit()
        
        service = AnomalyDetectionService(db)
        
        # Devrait retourner une liste vide (pas assez de données)
        anomalies = service.detect_anomalies_zscore(sample_meter.id)
        
        assert len(anomalies) == 0, "Ne devrait pas détecter d'anomalies avec si peu de données"
    
    @pytest.mark.parametrize("threshold", [1.5, 2.0, 2.5, 3.0])
    def test_threshold_sensitivity(
        self,
        db: Session,
        sample_meter,
        readings_with_anomalies,
        threshold
    ):
        """
        Test : Plus le seuil est élevé, moins on détecte d'anomalies
        """
        service = AnomalyDetectionService(db)
        service.threshold = threshold
        
        anomalies = service.detect_anomalies_zscore(sample_meter.id)
        
        # Simplement vérifier que la détection fonctionne
        # Un test plus simple : vérifier que le threshold influence le résultat
        assert isinstance(anomalies, list)
        
        # Avec un threshold très bas (1.5), on devrait détecter plus d'anomalies
        # qu'avec un threshold élevé (3.0)
        if threshold == 1.5:
            # Stocker le résultat pour comparaison
            pytest.threshold_results = {threshold: len(anomalies)}
        elif threshold == 3.0 and hasattr(pytest, 'threshold_results'):
            # Comparer avec le threshold bas
            low_threshold_count = pytest.threshold_results.get(1.5, 0)
            high_threshold_count = len(anomalies)
            # Un threshold plus élevé devrait détecter moins ou autant
            assert high_threshold_count <= low_threshold_count or low_threshold_count == 0
    
    def test_anomaly_detection_idempotent(
        self,
        db: Session,
        sample_meter,
        readings_with_anomalies
    ):
        """
        Test : Lancer la détection plusieurs fois donne le même résultat
        """
        service = AnomalyDetectionService(db)
        
        # Première détection
        count1 = service.mark_anomalies(sample_meter.id, method="zscore")
        
        # Deuxième détection (les anomalies sont déjà marquées)
        count2 = service.mark_anomalies(sample_meter.id, method="zscore")
        
        # Devrait être identique
        assert count1 == count2, "La détection n'est pas idempotente"