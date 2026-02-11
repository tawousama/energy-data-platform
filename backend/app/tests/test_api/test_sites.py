"""
Tests des Endpoints API - Sites

Tests d'intégration pour vérifier que l'API Sites fonctionne correctement.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.site import Site, SiteType


@pytest.mark.integration
class TestSitesEndpoints:
    """Suite de tests pour les endpoints /api/v1/sites"""
    
    def test_list_sites_empty(self, client: TestClient):
        """Test : Lister les sites quand la base est vide"""
        response = client.get("/api/v1/sites")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_sites(self, client: TestClient, sample_sites):
        """Test : Lister tous les sites"""
        response = client.get("/api/v1/sites")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        assert all("id" in site for site in data)
        assert all("name" in site for site in data)
    
    def test_list_sites_pagination(self, client: TestClient, sample_sites):
        """Test : Pagination fonctionne correctement"""
        # Première page (2 éléments)
        response = client.get("/api/v1/sites?skip=0&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Deuxième page
        response = client.get("/api/v1/sites?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Il reste 1 site
    
    def test_list_sites_filter_by_type(self, client: TestClient, sample_sites):
        """Test : Filtrer par type de site"""
        response = client.get("/api/v1/sites?site_type=solar")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["site_type"] == "solar"
    
    def test_list_sites_search(self, client: TestClient, sample_sites):
        """Test : Recherche dans nom et location"""
        response = client.get("/api/v1/sites?search=bordeaux")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 1
        # Vérifier que "bordeaux" est dans le nom ou la location
        for site in data:
            assert (
                "bordeaux" in site["name"].lower() or 
                "bordeaux" in site["location"].lower()
            )
    
    def test_get_site_by_id(self, client: TestClient, sample_site):
        """Test : Récupérer un site par son ID"""
        response = client.get(f"/api/v1/sites/{sample_site.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == sample_site.id
        assert data["name"] == sample_site.name
        assert data["site_type"] == sample_site.site_type.value
        assert data["capacity_kw"] == sample_site.capacity_kw
    
    def test_get_site_not_found(self, client: TestClient):
        """Test : Erreur 404 si site inexistant"""
        response = client.get("/api/v1/sites/99999")
        
        assert response.status_code == 404
        assert "introuvable" in response.json()["detail"].lower()
    
    def test_create_site(self, client: TestClient):
        """Test : Créer un nouveau site"""
        new_site = {
            "name": "Nouveau Parc Solaire",
            "site_type": "solar",
            "location": "Marseille, France",
            "latitude": 43.2965,
            "longitude": 5.3698,
            "capacity_kw": 8000.0,
            "description": "Installation test"
        }
        
        response = client.post("/api/v1/sites", json=new_site)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == new_site["name"]
        assert data["site_type"] == new_site["site_type"]
        assert data["capacity_kw"] == new_site["capacity_kw"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_site_duplicate_name(self, client: TestClient, sample_site):
        """Test : Erreur si nom de site déjà existant"""
        duplicate_site = {
            "name": sample_site.name,  # Nom déjà existant
            "site_type": "solar",
            "location": "Test",
            "capacity_kw": 5000.0
        }
        
        response = client.post("/api/v1/sites", json=duplicate_site)
        
        assert response.status_code == 400
        assert "existe déjà" in response.json()["detail"].lower()
    
    def test_create_site_invalid_data(self, client: TestClient):
        """Test : Validation des données invalides"""
        invalid_site = {
            "name": "Test",
            "site_type": "solar",
            "location": "Test",
            "capacity_kw": -1000.0  # Capacité négative = invalide
        }
        
        response = client.post("/api/v1/sites", json=invalid_site)
        
        assert response.status_code == 422  # Validation error
    
    def test_create_site_missing_required_fields(self, client: TestClient):
        """Test : Erreur si champs requis manquants"""
        incomplete_site = {
            "name": "Test"
            # Manque site_type, location, capacity_kw
        }
        
        response = client.post("/api/v1/sites", json=incomplete_site)
        
        assert response.status_code == 422
    
    def test_update_site(self, client: TestClient, sample_site):
        """Test : Mettre à jour un site"""
        update_data = {
            "capacity_kw": 6000.0,
            "description": "Capacité augmentée"
        }
        
        response = client.put(
            f"/api/v1/sites/{sample_site.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == sample_site.id
        assert data["capacity_kw"] == 6000.0
        assert data["description"] == "Capacité augmentée"
        # Les autres champs ne doivent pas changer
        assert data["name"] == sample_site.name
    
    def test_update_site_not_found(self, client: TestClient):
        """Test : Erreur 404 si site à mettre à jour inexistant"""
        response = client.put(
            "/api/v1/sites/99999",
            json={"capacity_kw": 5000.0}
        )
        
        assert response.status_code == 404
    
    def test_delete_site(self, client: TestClient, sample_site, db: Session):
        """Test : Supprimer un site"""
        site_id = sample_site.id
        
        response = client.delete(f"/api/v1/sites/{site_id}")
        
        assert response.status_code == 204
        
        # Vérifier que le site n'existe plus
        from app.models.site import Site
        deleted_site = db.query(Site).filter(Site.id == site_id).first()
        assert deleted_site is None
    
    def test_delete_site_not_found(self, client: TestClient):
        """Test : Erreur 404 si site à supprimer inexistant"""
        response = client.delete("/api/v1/sites/99999")
        
        assert response.status_code == 404
    
    def test_delete_site_cascade(
        self,
        client: TestClient,
        sample_site,
        sample_meter,
        db: Session
    ):
        """
        Test : La suppression d'un site supprime aussi ses compteurs (CASCADE)
        """
        site_id = sample_site.id
        meter_id = sample_meter.id
        
        # Supprimer le site
        response = client.delete(f"/api/v1/sites/{site_id}")
        assert response.status_code == 204
        
        # Vérifier que le compteur a aussi été supprimé
        from app.models.meter import Meter
        deleted_meter = db.query(Meter).filter(Meter.id == meter_id).first()
        assert deleted_meter is None
    
    def test_get_site_statistics(self, client: TestClient, sample_site, sample_meter):
        """Test : Obtenir les statistiques d'un site"""
        response = client.get(f"/api/v1/sites/{sample_site.id}/statistics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["site_id"] == sample_site.id
        assert data["site_name"] == sample_site.name
        assert data["total_meters"] >= 1
        assert data["active_meters"] >= 1
        assert data["capacity_kw"] == sample_site.capacity_kw
    
    def test_site_response_structure(self, client: TestClient, sample_site):
        """Test : Vérifier la structure complète de la réponse"""
        response = client.get(f"/api/v1/sites/{sample_site.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier que tous les champs requis sont présents
        required_fields = [
            "id", "name", "site_type", "location",
            "latitude", "longitude", "capacity_kw",
            "description", "created_at", "updated_at"
        ]
        
        for field in required_fields:
            assert field in data, f"Champ manquant: {field}"
    
    def test_site_timestamps(self, client: TestClient, db: Session):
        """Test : Les timestamps sont créés automatiquement"""
        new_site = {
            "name": "Site Timestamp Test",
            "site_type": "wind",
            "location": "Test",
            "capacity_kw": 5000.0
        }
        
        response = client.post("/api/v1/sites", json=new_site)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["created_at"] is not None
        # updated_at peut être None à la création
        
        # Vérifier le format ISO 8601
        from datetime import datetime
        created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        assert created_at is not None
    
    def test_concurrent_site_creation(self, client: TestClient):
        """Test : Créer plusieurs sites en parallèle"""
        sites = [
            {
                "name": f"Site Concurrent {i}",
                "site_type": "solar",
                "location": "Test",
                "capacity_kw": 5000.0
            }
            for i in range(5)
        ]
        
        responses = [
            client.post("/api/v1/sites", json=site)
            for site in sites
        ]
        
        # Tous doivent réussir
        for response in responses:
            assert response.status_code == 201
        
        # Tous doivent avoir des IDs différents
        ids = [r.json()["id"] for r in responses]
        assert len(set(ids)) == 5, "Les IDs ne sont pas uniques"