"""
Tests des Endpoints API - Consumption

Tests d'intégration pour les lectures et agrégations de consommation.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.consumption import ConsumptionReading


@pytest.mark.integration
class TestConsumptionEndpoints:
    """Suite de tests pour les endpoints /api/v1/consumption"""
    
    def test_get_readings_empty(self, client: TestClient):
        """Test : Liste vide si aucune lecture"""
        response = client.get("/api/v1/consumption/readings")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_readings(self, client: TestClient, sample_readings):
        """Test : Récupérer toutes les lectures"""
        response = client.get("/api/v1/consumption/readings")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) > 0
        assert all("id" in reading for reading in data)
        assert all("value_kwh" in reading for reading in data)
    
    def test_get_readings_filter_by_meter(
        self,
        client: TestClient,
        sample_meter,
        sample_readings
    ):
        """Test : Filtrer par compteur"""
        response = client.get(
            f"/api/v1/consumption/readings?meter_id={sample_meter.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Toutes les lectures doivent être du même compteur
        assert all(r["meter_id"] == sample_meter.id for r in data)
    
    def test_get_readings_filter_by_date(
        self,
        client: TestClient,
        sample_meter,
        sample_readings
    ):
        """Test : Filtrer par date"""
        # Date de début : il y a 3 jours
        start_date = (datetime.utcnow() - timedelta(days=3)).isoformat()
        
        response = client.get(
            f"/api/v1/consumption/readings"
            f"?meter_id={sample_meter.id}"
            f"&start_date={start_date}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier que toutes les lectures sont après la date de début
        for reading in data:
            reading_date_str = reading["timestamp"].replace("Z", "+00:00")
            reading_date = datetime.fromisoformat(reading_date_str)
            filter_date = datetime.fromisoformat(start_date)
            
            # Comparer en ignorant la timezone (comparer seulement les dates)
            assert reading_date.replace(tzinfo=None) >= filter_date.replace(tzinfo=None)
    
    def test_get_readings_only_anomalies(
        self,
        client: TestClient,
        sample_meter,
        db: Session
    ):
        """Test : Filtrer uniquement les anomalies"""
        # Créer quelques lectures avec anomalies
        for i in range(5):
            reading = ConsumptionReading(
                meter_id=sample_meter.id,
                timestamp=datetime.utcnow() + timedelta(hours=i),
                value_kwh=100.0,
                is_anomaly=(i % 2 == 0)  # 1 sur 2 est une anomalie
            )
            db.add(reading)
        db.commit()
        
        response = client.get(
            f"/api/v1/consumption/readings"
            f"?meter_id={sample_meter.id}"
            f"&only_anomalies=true"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Toutes doivent être des anomalies
        assert all(r["is_anomaly"] is True for r in data)
    
    def test_get_readings_pagination(
        self,
        client: TestClient,
        sample_readings
    ):
        """Test : Pagination des lectures"""
        # Première page
        response = client.get("/api/v1/consumption/readings?skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        
        # Deuxième page
        response = client.get("/api/v1/consumption/readings?skip=10&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
    
    def test_create_reading(self, client: TestClient, sample_meter):
        """Test : Créer une nouvelle lecture"""
        new_reading = {
            "meter_id": sample_meter.id,
            "timestamp": datetime.utcnow().isoformat(),
            "value_kwh": 125.5
        }
        
        response = client.post(
            "/api/v1/consumption/readings",
            json=new_reading
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["meter_id"] == new_reading["meter_id"]
        assert data["value_kwh"] == new_reading["value_kwh"]
        assert "id" in data
        assert data["is_anomaly"] is False  # Par défaut
    
    def test_create_reading_invalid_meter(self, client: TestClient):
        """Test : Erreur si compteur inexistant"""
        new_reading = {
            "meter_id": 99999,  # Compteur inexistant
            "timestamp": datetime.utcnow().isoformat(),
            "value_kwh": 125.5
        }
        
        response = client.post(
            "/api/v1/consumption/readings",
            json=new_reading
        )
        
        assert response.status_code == 404
    
    def test_create_reading_negative_value(self, client: TestClient, sample_meter):
        """Test : Validation - valeur négative interdite"""
        invalid_reading = {
            "meter_id": sample_meter.id,
            "timestamp": datetime.utcnow().isoformat(),
            "value_kwh": -100.0  # Invalide
        }
        
        response = client.post(
            "/api/v1/consumption/readings",
            json=invalid_reading
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_hourly_aggregation(
        self,
        client: TestClient,
        sample_meter,
        sample_readings
    ):
        """Test : Agrégation horaire"""
        response = client.get(
            f"/api/v1/consumption/aggregated/hourly"
            f"?meter_id={sample_meter.id}"
            f"&days=7"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) > 0
        
        # Vérifier la structure
        for item in data:
            assert "period" in item
            assert "total_kwh" in item
            assert "average_kwh" in item
            assert "min_kwh" in item
            assert "max_kwh" in item
            assert "reading_count" in item
            
            # Vérifier les valeurs
            assert item["total_kwh"] >= 0
            assert item["average_kwh"] >= 0
            assert item["reading_count"] > 0
    
    def test_daily_aggregation(
        self,
        client: TestClient,
        sample_meter,
        sample_readings
    ):
        """Test : Agrégation journalière"""
        response = client.get(
            f"/api/v1/consumption/aggregated/daily"
            f"?meter_id={sample_meter.id}"
            f"&days=7"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Devrait avoir environ 7 jours (peut être 8 si on compte une journée partielle)
        assert 7 <= len(data) <= 8, f"Attendu 7-8 jours, obtenu {len(data)}"
        assert len(data) > 0
        
        # Vérifier que les périodes sont des dates
        for item in data:
            # Format : "2024-01-15"
            assert len(item["period"]) == 10
            assert item["period"].count("-") == 2
    
    def test_aggregation_invalid_meter(self, client: TestClient):
        """Test : Erreur si compteur inexistant pour agrégation"""
        response = client.get(
            "/api/v1/consumption/aggregated/hourly?meter_id=99999"
        )
        
        # Devrait retourner une liste vide, pas d'erreur
        assert response.status_code == 200
        assert response.json() == []
    
    def test_consumption_stats(
        self,
        client: TestClient,
        sample_meter,
        sample_readings
    ):
        """Test : Statistiques de consommation"""
        response = client.get(
            f"/api/v1/consumption/stats/{sample_meter.id}?days=7"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier la structure
        assert "meter_id" in data
        assert "period_days" in data
        assert "total_kwh" in data
        assert "daily_average_kwh" in data
        assert "peak_kwh" in data
        assert "anomaly_count" in data
        
        # Vérifier les valeurs
        assert data["meter_id"] == sample_meter.id
        assert data["period_days"] == 7
        assert data["total_kwh"] > 0
        assert data["daily_average_kwh"] > 0
        assert data["peak_kwh"] > 0
        assert data["anomaly_count"] >= 0
    
    def test_reading_response_structure(
        self,
        client: TestClient,
        sample_readings
    ):
        """Test : Structure complète d'une lecture"""
        response = client.get("/api/v1/consumption/readings?limit=1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        reading = data[0]
        
        # Champs requis
        required_fields = [
            "id", "meter_id", "timestamp", "value_kwh",
            "is_anomaly", "anomaly_score", "created_at"
        ]
        
        for field in required_fields:
            assert field in reading, f"Champ manquant: {field}"
    
    def test_readings_ordered_by_timestamp_desc(
        self,
        client: TestClient,
        sample_readings
    ):
        """Test : Les lectures sont triées par date décroissante"""
        response = client.get("/api/v1/consumption/readings?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier l'ordre décroissant
        timestamps = [
            datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00"))
            for r in data
        ]
        
        for i in range(len(timestamps) - 1):
            assert timestamps[i] >= timestamps[i + 1], \
                "Les lectures ne sont pas triées par date décroissante"
    
    def test_aggregation_values_consistency(
        self,
        client: TestClient,
        sample_meter,
        sample_readings
    ):
        """
        Test : Les valeurs agrégées sont cohérentes
        (min <= average <= max)
        """
        response = client.get(
            f"/api/v1/consumption/aggregated/hourly"
            f"?meter_id={sample_meter.id}&days=1"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for item in data:
            min_val = item["min_kwh"]
            avg_val = item["average_kwh"]
            max_val = item["max_kwh"]
            
            assert min_val <= avg_val <= max_val, \
                f"Incohérence: min={min_val}, avg={avg_val}, max={max_val}"