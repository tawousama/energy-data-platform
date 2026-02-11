"""
Fixtures Pytest Globales

Ces fixtures sont disponibles pour tous les tests.
"""

import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models.site import Site, SiteType
from app.models.meter import Meter
from app.models.consumption import ConsumptionReading
from datetime import datetime, timedelta


# === BASE DE DONNÉES DE TEST ===

# URL de la base de données de test
# IMPORTANT : Utilisez une base séparée pour les tests !
import os

# Essayer de lire depuis les variables d'environnement ou utiliser par défaut
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://energy_user:energy_password@localhost:5432/energy_db_test"
)

# Créer le moteur de test
test_engine = create_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)

# Factory de sessions pour les tests
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def db_engine():
    """
    Fixture session-level : crée les tables une fois au début des tests.
    
    Scope 'session' = exécuté une seule fois pour toute la session de tests.
    """
    print("\n🏗️  Création des tables de test...")
    
    # Importer tous les modèles pour qu'ils soient enregistrés
    from app.models.site import Site
    from app.models.meter import Meter
    from app.models.consumption import ConsumptionReading
    
    # Créer toutes les tables
    Base.metadata.create_all(bind=test_engine)
    print("✅ Tables de test créées")
    
    yield test_engine
    
    # Supprimer toutes les tables à la fin
    print("\n🗑️  Suppression des tables de test...")
    Base.metadata.drop_all(bind=test_engine)
    print("✅ Tables de test supprimées")


@pytest.fixture(scope="function")
def db(db_engine) -> Generator[Session, None, None]:
    """
    Fixture function-level : fournit une session DB propre pour chaque test.
    
    Scope 'function' = nouvelle session pour chaque fonction de test.
    Les modifications sont automatiquement annulées après le test.
    
    Usage:
        def test_something(db):
            site = Site(name="Test")
            db.add(site)
            db.commit()
            # Les données seront rollback après le test
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    
    yield session
    
    # Rollback automatique après chaque test
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Fixture pour tester l'API avec FastAPI TestClient.
    
    Override la dépendance get_db pour utiliser notre session de test.
    
    Usage:
        def test_api_endpoint(client):
            response = client.get("/api/v1/sites")
            assert response.status_code == 200
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# === FIXTURES DE DONNÉES ===

@pytest.fixture
def sample_site(db: Session) -> Site:
    """
    Crée un site de test simple.
    
    Usage:
        def test_with_site(sample_site):
            assert sample_site.id is not None
    """
    site = Site(
        name="Test Solar Farm",
        site_type=SiteType.SOLAR,
        location="Paris, France",
        latitude=48.8566,
        longitude=2.3522,
        capacity_kw=5000.0,
        description="Site de test"
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@pytest.fixture
def sample_sites(db: Session) -> list[Site]:
    """
    Crée plusieurs sites de test.
    
    Returns:
        Liste de 3 sites
    """
    sites = [
        Site(
            name="Parc Solaire Test",
            site_type=SiteType.SOLAR,
            location="Bordeaux, France",
            latitude=44.8378,
            longitude=-0.5792,
            capacity_kw=5000.0
        ),
        Site(
            name="Ferme Éolienne Test",
            site_type=SiteType.WIND,
            location="Brest, France",
            latitude=48.3905,
            longitude=-4.4861,
            capacity_kw=75000.0
        ),
        Site(
            name="Usine Test",
            site_type=SiteType.CONSUMER,
            location="Lyon, France",
            latitude=45.7640,
            longitude=4.8357,
            capacity_kw=25000.0
        )
    ]
    
    for site in sites:
        db.add(site)
    
    db.commit()
    
    for site in sites:
        db.refresh(site)
    
    return sites


@pytest.fixture
def sample_meter(db: Session, sample_site: Site) -> Meter:
    """
    Crée un compteur de test associé à un site.
    """
    meter = Meter(
        site_id=sample_site.id,
        meter_id="TEST_METER_001",
        meter_type="production",
        is_active=True
    )
    db.add(meter)
    db.commit()
    db.refresh(meter)
    return meter


@pytest.fixture
def sample_readings(db: Session, sample_meter: Meter) -> list[ConsumptionReading]:
    """
    Crée des lectures de test pour un compteur.
    
    Génère 7 jours de données (1 par heure = 168 lectures).
    """
    readings = []
    base_time = datetime.utcnow() - timedelta(days=7)
    
    for day in range(7):
        for hour in range(24):
            timestamp = base_time + timedelta(days=day, hours=hour)
            value = 100.0 + (hour * 2)  # Pattern simple
            
            reading = ConsumptionReading(
                meter_id=sample_meter.id,
                timestamp=timestamp,
                value_kwh=value
            )
            readings.append(reading)
            db.add(reading)
    
    db.commit()
    
    for reading in readings:
        db.refresh(reading)
    
    return readings


@pytest.fixture
def readings_with_anomalies(db: Session, sample_meter: Meter) -> list[ConsumptionReading]:
    """
    Crée des lectures avec anomalies intentionnelles.
    
    Pattern :
    - Valeurs normales : ~100 kWh
    - Anomalies aux positions [24, 48, 72] : ~300 kWh
    """
    readings = []
    base_time = datetime.utcnow() - timedelta(days=7)
    anomaly_positions = [24, 48, 72]  # Heures avec anomalies
    
    for hour in range(168):  # 7 jours * 24 heures
        timestamp = base_time + timedelta(hours=hour)
        
        # Injecter une anomalie à certaines positions
        if hour in anomaly_positions:
            value = 300.0  # Valeur anormalement haute
        else:
            value = 100.0 + (hour % 24) * 2  # Valeur normale
        
        reading = ConsumptionReading(
            meter_id=sample_meter.id,
            timestamp=timestamp,
            value_kwh=value
        )
        readings.append(reading)
        db.add(reading)
    
    db.commit()
    
    for reading in readings:
        db.refresh(reading)
    
    return readings


# === FIXTURES UTILITAIRES ===

@pytest.fixture
def api_headers():
    """Headers HTTP standards pour les requêtes API"""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


# === MARKERS PYTEST ===

def pytest_configure(config):
    """
    Configuration supplémentaire de pytest.
    
    Définit les markers personnalisés.
    """
    config.addinivalue_line(
        "markers",
        "unit: Tests unitaires (logique isolée)"
    )
    config.addinivalue_line(
        "markers",
        "integration: Tests d'intégration (API + DB)"
    )
    config.addinivalue_line(
        "markers",
        "slow: Tests lents (skip avec -m 'not slow')"
    )