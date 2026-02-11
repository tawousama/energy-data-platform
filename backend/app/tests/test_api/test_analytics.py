"""
Tests des Endpoints API - Analytics

Tests d'intégration pour la détection d'anomalies via l'API.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.consumption import ConsumptionReading


@pytest.mark.integration
class TestAnalyticsEndpoints:
    """Suite de tests pour les endpoints /api/v1/analytics"""
    
    def test_detect_anomalies_zscore(
        self,
        client: TestClient,
        sample_meter,
        readings_with_anomalies
    ):
        """Test : Détecter les anomalies avec la méthode Z-score"""
        response = client.post(
            f"/api/v1/analytics/anomalies/detect/{sample_meter.id}"
            f"?method=zscore"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier la structure
        assert "meter_id" in data
        assert "method" in data
        assert "anomalies_detected" in data
        assert "message" in data
        
        # Vérifier les valeurs
        assert data["meter_id"] == sample_meter.id
        assert data["method"] == "zscore"
        assert data["anomalies_detected"] > 0  # On a injecté des anomalies
    
    def test_detect_anomalies_iqr(
        self,
        client: TestClient,
        sample_meter,
        readings_with_anomalies
    ):
        """Test : Détecter avec la méthode IQR"""
        response = client.post(
            f"/api/v1/analytics/anomalies/detect/{sample_meter.id}"
            f"?method=iqr"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["method"] == "iqr"
        assert data["anomalies_detected"] >= 0
    
    def test_detect_anomalies_moving_average(
        self,
        client: TestClient,
        sample_meter,
        readings_with_anomalies
    ):
        """Test : Détecter avec la méthode Moving Average"""
        response = client.post(
            f"/api/v1/analytics/anomalies/detect/{sample_meter.id}"
            f"?method=moving_average"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["method"] == "moving_average"
    
    def test_detect_anomalies_invalid_method(
        self,
        client: TestClient,
        sample_meter
    ):
        """Test : Erreur si méthode invalide"""
        response = client.post(
            f"/api/v1/analytics/anomalies/detect/{sample_meter.id}"
            f"?method=invalid_method"
        )
        
        # Devrait être rejeté par la validation
        assert response.status_code == 422
    
    def test_detect_anomalies_meter_not_found(self, client: TestClient):
        """Test : Erreur 404 si compteur inexistant"""
        response = client.post(
            "/api/v1/analytics/anomalies/detect/99999?method=zscore"
        )
        
        assert response.status_code == 404
    
    def test_detect_anomalies_updates_database(
        self,
        client: TestClient,
        sample_meter,
        readings_with_anomalies,
        db: Session
    ):
        """Test : La détection met bien à jour la base de données"""
        # Avant : aucune anomalie marquée
        count_before = db.query(ConsumptionReading).filter(
            ConsumptionReading.meter_id == sample_meter.id,
            ConsumptionReading.is_anomaly == True
        ).count()
        assert count_before == 0
        
        # Déclencher la détection
        response = client.post(
            f"/api/v1/analytics/anomalies/detect/{sample_meter.id}"
            f"?method=zscore"
        )
        
        assert response.status_code == 200
        detected_count = response.json()["anomalies_detected"]
        
        # Après : anomalies marquées
        count_after = db.query(ConsumptionReading).filter(
            ConsumptionReading.meter_id == sample_meter.id,
            ConsumptionReading.is_anomaly == True
        ).count()
        
        assert count_after == detected_count
        assert count_after > 0
    
    def test_get_anomaly_summary(
        self,
        client: TestClient,
        sample_meter,
        readings_with_anomalies
    ):
        """Test : Obtenir le résumé des anomalies"""
        # D'abord détecter les anomalies
        client.post(
            f"/api/v1/analytics/anomalies/detect/{sample_meter.id}"
            f"?method=zscore"
        )
        
        # Puis obtenir le résumé
        response = client.get(
            f"/api/v1/analytics/anomalies/summary/{sample_meter.id}"
            f"?days=7"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier la structure
        assert "meter_id" in data
        assert "period_days" in data
        assert "total_readings" in data
        assert "anomaly_count" in data
        assert "anomaly_rate" in data
        
        # Vérifier les valeurs
        assert data["meter_id"] == sample_meter.id
        assert data["period_days"] == 7
        assert data["total_readings"] > 0
        assert data["anomaly_count"] >= 0
        assert 0 <= data["anomaly_rate"] <= 1
    
    def test_get_anomaly_summary_meter_not_found(self, client: TestClient):
        """Test : Erreur 404 si compteur inexistant"""
        response = client.get(
            "/api/v1/analytics/anomalies/summary/99999"
        )
        
        assert response.status_code == 404
    
    def test_get_recent_anomalies(
        self,
        client: TestClient,
        sample_meter,
        readings_with_anomalies
    ):
        """Test : Obtenir les anomalies récentes"""
        # Détecter d'abord
        client.post(
            f"/api/v1/analytics/anomalies/detect/{sample_meter.id}"
            f"?method=zscore"
        )
        
        # Récupérer les anomalies récentes
        response = client.get(
            "/api/v1/analytics/anomalies/recent?hours=24&limit=10"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier la structure
        assert "period_hours" in data
        assert "total_anomalies" in data
        assert "anomalies" in data
        
        assert data["period_hours"] == 24
        assert isinstance(data["anomalies"], list)
        
        # Si des anomalies sont trouvées, vérifier leur structure
        if data["total_anomalies"] > 0:
            anomaly = data["anomalies"][0]
            assert "reading_id" in anomaly
            assert "meter_id" in anomaly
            assert "timestamp" in anomaly
            assert "value_kwh" in anomaly
            assert "anomaly_score" in anomaly
            assert "severity" in anomaly
    
    def test_reset_anomalies(
        self,
        client: TestClient,
        sample_meter,
        readings_with_anomalies,
        db: Session
    ):
        """Test : Réinitialiser les flags d'anomalies"""
        # Détecter les anomalies
        client.post(
            f"/api/v1/analytics/anomalies/detect/{sample_meter.id}"
            f"?method=zscore"
        )
        
        # Vérifier qu'il y a des anomalies
        count_before = db.query(ConsumptionReading).filter(
            ConsumptionReading.meter_id == sample_meter.id,
            ConsumptionReading.is_anomaly == True
        ).count()
        assert count_before > 0
        
        # Réinitialiser
        response = client.delete(
            f"/api/v1/analytics/anomalies/reset/{sample_meter.id}"
        )
        
        assert response.status_code == 204
        
        # Vérifier qu'il n'y a plus d'anomalies marquées
        count_after = db.query(ConsumptionReading).filter(
            ConsumptionReading.meter_id == sample_meter.id,
            ConsumptionReading.is_anomaly == True
        ).count()
        assert count_after == 0
    
    def test_reset_anomalies_meter_not_found(self, client: TestClient):
        """Test : Erreur 404 si compteur inexistant"""
        response = client.delete(
            "/api/v1/analytics/anomalies/reset/99999"
        )
        
        assert response.status_code == 404
    
    def test_anomaly_detection_idempotent(
        self,
        client: TestClient,
        sample_meter,
        readings_with_anomalies
    ):
        """Test : Détecter plusieurs fois donne le même résultat"""
        # Première détection
        response1 = client.post(
            f"/api/v1/analytics/anomalies/detect/{sample_meter.id}"
            f"?method=zscore"
        )
        count1 = response1.json()["anomalies_detected"]
        
        # Deuxième détection
        response2 = client.post(
            f"/api/v1/analytics/anomalies/detect/{sample_meter.id}"
            f"?method=zscore"
        )
        count2 = response2.json()["anomalies_detected"]
        
        # Devrait être identique
        assert count1 == count2
    
    def test_different_methods_different_results(
        self,
        client: TestClient,
        sample_meter,
        readings_with_anomalies
    ):
        """
        Test : Différentes méthodes peuvent donner des résultats différents
        """
        # Réinitialiser d'abord
        client.delete(
            f"/api/v1/analytics/anomalies/reset/{sample_meter.id}"
        )
        
        # Détecter avec Z-score
        response_zscore = client.post(
            f"/api/v1/analytics/anomalies/detect/{sample_meter.id}"
            f"?method=zscore"
        )
        count_zscore = response_zscore.json()["anomalies_detected"]
        
        # Réinitialiser
        client.delete(
            f"/api/v1/analytics/anomalies/reset/{sample_meter.id}"
        )
        
        # Détecter avec IQR
        response_iqr = client.post(
            f"/api/v1/analytics/anomalies/detect/{sample_meter.id}"
            f"?method=iqr"
        )
        count_iqr = response_iqr.json()["anomalies_detected"]
        
        # Les résultats peuvent être différents (pas forcément, mais c'est OK)
        assert count_zscore >= 0
        assert count_iqr >= 0
    
    def test_anomaly_severity_classification(
        self,
        client: TestClient,
        sample_meter,
        readings_with_anomalies
    ):
        """Test : La sévérité des anomalies est bien classifiée"""
        # Détecter
        client.post(
            f"/api/v1/analytics/anomalies/detect/{sample_meter.id}"
            f"?method=zscore"
        )
        
        # Récupérer les anomalies récentes
        response = client.get(
            "/api/v1/analytics/anomalies/recent?hours=168"  # 7 jours
        )
        
        data = response.json()
        
        if data["total_anomalies"] > 0:
            for anomaly in data["anomalies"]:
                severity = anomaly["severity"]
                score = anomaly["anomaly_score"]
                
                # Vérifier la cohérence de la classification
                if score > 4:
                    assert severity == "critique"
                elif score > 3:
                    assert severity == "élevée"
                else:
                    assert severity == "modérée"