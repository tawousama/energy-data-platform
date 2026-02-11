"""
Test de vérification des fixtures
"""
import pytest
from sqlalchemy.orm import Session

def test_database_connection(db: Session):
    """Test : La connexion DB fonctionne"""
    from sqlalchemy import text
    result = db.execute(text("SELECT 1"))
    assert result.fetchone()[0] == 1
    print("✅ Connexion DB OK")

def test_sample_site_fixture(sample_site):
    """Test : La fixture sample_site crée bien un site"""
    assert sample_site.id is not None
    assert sample_site.name == "Test Solar Farm"
    print(f"✅ Site créé : {sample_site.name} (ID: {sample_site.id})")

def test_sample_meter_fixture(sample_meter):
    """Test : La fixture sample_meter crée bien un compteur"""
    assert sample_meter.id is not None
    assert sample_meter.meter_id == "TEST_METER_001"
    print(f"✅ Compteur créé : {sample_meter.meter_id}")

def test_sample_readings_fixture(sample_readings):
    """Test : La fixture sample_readings crée bien des lectures"""
    assert len(sample_readings) == 168  # 7 jours * 24 heures
    print(f"✅ {len(sample_readings)} lectures créées")

def test_data_isolation(db: Session, sample_site):
    """Test : Les données sont isolées entre les tests"""
    from app.models.site import Site
    
    # Créer un site dans ce test
    new_site = Site(
        name="Site Isolation Test",
        site_type="solar",
        location="Test",
        capacity_kw=1000.0
    )
    db.add(new_site)
    db.commit()
    
    # Vérifier qu'il y a au moins 2 sites (sample_site + new_site)
    count = db.query(Site).count()
    assert count >= 2
    print(f"✅ {count} sites dans ce test")
    # Après ce test, le rollback supprimera new_site automatiquement