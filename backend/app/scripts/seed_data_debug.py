"""
Script de Seed - Version avec Debug Amélioré

Ce script vérifie tout avant de créer les données.
"""

import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import random
import numpy as np

from app.core.database import SessionLocal, engine, Base
from app.models.site import Site, SiteType
from app.models.meter import Meter
from app.models.consumption import ConsumptionReading


def check_database_connection():
    """Vérifie que la connexion à la base fonctionne"""
    print("\n🔍 ÉTAPE 1 : Vérification de la connexion à la base...")
    
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✅ Connexion réussie!")
        print(f"   PostgreSQL: {version.split(',')[0]}")
        db.close()
        return True
    except Exception as e:
        print(f"❌ ERREUR de connexion:")
        print(f"   {e}")
        print("\n💡 Solutions:")
        print("   1. Vérifiez que PostgreSQL est démarré")
        print("   2. Vérifiez le fichier .env (DATABASE_URL)")
        print("   3. Vérifiez que la base 'energy_db' existe")
        return False


def check_tables_exist():
    """Vérifie que les tables existent"""
    print("\n🔍 ÉTAPE 2 : Vérification des tables...")
    
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ['sites', 'meters', 'consumption_readings']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print(f"❌ Tables manquantes: {missing_tables}")
            print(f"\n💡 Créez les tables avec:")
            print(f"   python -m app.scripts.init_database")
            print(f"\n   ou en Python:")
            print(f"   >>> from app.core.database import Base, engine")
            print(f"   >>> Base.metadata.create_all(engine)")
            return False
        else:
            print(f"✅ Toutes les tables existent: {tables}")
            return True
            
    except Exception as e:
        print(f"❌ ERREUR lors de la vérification des tables:")
        print(f"   {e}")
        return False


def clear_existing_data(db: Session):
    """Supprime les données existantes"""
    print("\n🗑️  ÉTAPE 3 : Suppression des données existantes...")
    
    try:
        # Compter avant suppression
        count_readings = db.query(ConsumptionReading).count()
        count_meters = db.query(Meter).count()
        count_sites = db.query(Site).count()
        
        print(f"   Données actuelles:")
        print(f"   • Sites: {count_sites}")
        print(f"   • Compteurs: {count_meters}")
        print(f"   • Lectures: {count_readings}")
        
        # Supprimer dans l'ordre (à cause des foreign keys)
        db.query(ConsumptionReading).delete()
        db.query(Meter).delete()
        db.query(Site).delete()
        db.commit()
        
        print(f"✅ Données supprimées")
        return True
        
    except Exception as e:
        print(f"❌ ERREUR lors de la suppression:")
        print(f"   {e}")
        db.rollback()
        return False


def create_sites(db: Session):
    """Crée les sites"""
    print("\n📍 ÉTAPE 4 : Création des sites...")
    
    sites_data = [
        {
            "name": "Parc Solaire Bordeaux",
            "site_type": SiteType.SOLAR,
            "location": "Bordeaux, France",
            "latitude": 44.8378,
            "longitude": -0.5792,
            "capacity_kw": 5000.0,
            "description": "Installation de 150 panneaux"
        },
        {
            "name": "Ferme Éolienne Bretagne",
            "site_type": SiteType.WIND,
            "location": "Finistère, France",
            "latitude": 48.6667,
            "longitude": -4.1667,
            "capacity_kw": 75000.0,
            "description": "50 éoliennes offshore"
        },
        {
            "name": "Centrale Hydro Alpes",
            "site_type": SiteType.HYDRO,
            "location": "Savoie, France",
            "latitude": 45.6197,
            "longitude": 6.7697,
            "capacity_kw": 120000.0,
            "description": "Barrage sur l'Isère"
        },
        {
            "name": "Usine Automobile Lyon",
            "site_type": SiteType.CONSUMER,
            "location": "Lyon, France",
            "latitude": 45.7640,
            "longitude": 4.8357,
            "capacity_kw": 25000.0,
            "description": "Site de production"
        },
        {
            "name": "Data Center Paris",
            "site_type": SiteType.CONSUMER,
            "location": "Paris, France",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "capacity_kw": 15000.0,
            "description": "Centre de données"
        }
    ]
    
    sites = []
    try:
        for data in sites_data:
            site = Site(**data)
            db.add(site)
            sites.append(site)
            print(f"   ✓ {data['name']}")
        
        db.commit()
        # Rafraîchir pour obtenir les IDs
        for site in sites:
            db.refresh(site)
        
        print(f"✅ {len(sites)} sites créés")
        return sites
        
    except Exception as e:
        print(f"❌ ERREUR lors de la création des sites:")
        print(f"   {e}")
        db.rollback()
        return []


def create_meters(db: Session, sites):
    """Crée les compteurs"""
    print("\n📟 ÉTAPE 5 : Création des compteurs...")
    
    if not sites:
        print("❌ Pas de sites disponibles")
        return []
    
    meters = []
    try:
        for site in sites:
            # 2 compteurs par site pour simplifier
            for i in range(2):
                meter_type = "production" if site.site_type in [SiteType.SOLAR, SiteType.WIND, SiteType.HYDRO] else "consumption"
                
                meter = Meter(
                    site_id=site.id,
                    meter_id=f"{site.site_type.value.upper()}_{site.id:03d}_{i+1:02d}",
                    meter_type=meter_type,
                    is_active=True
                )
                db.add(meter)
                meters.append(meter)
        
        db.commit()
        # Rafraîchir pour obtenir les IDs
        for meter in meters:
            db.refresh(meter)
        
        print(f"✅ {len(meters)} compteurs créés")
        return meters
        
    except Exception as e:
        print(f"❌ ERREUR lors de la création des compteurs:")
        print(f"   {e}")
        db.rollback()
        return []


def create_readings(db: Session, meters, days=7):
    """Crée les lectures (version simplifiée pour debug)"""
    print(f"\n📊 ÉTAPE 6 : Création de {days} jours de données...")
    
    if not meters:
        print("❌ Pas de compteurs disponibles")
        return 0
    
    total = 0
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        for meter_idx, meter in enumerate(meters, 1):
            print(f"   📟 Compteur {meter_idx}/{len(meters)}: {meter.meter_id}")
            
            readings_batch = []
            
            # Simplifier : 1 lecture par heure au lieu de 4 par heure
            for day in range(days):
                for hour in range(24):
                    timestamp = start_date + timedelta(days=day, hours=hour)
                    
                    # Valeur simple
                    base_value = 100.0
                    value = base_value * (1 + random.uniform(-0.2, 0.2))
                    
                    reading = ConsumptionReading(
                        meter_id=meter.id,
                        timestamp=timestamp,
                        value_kwh=value
                    )
                    readings_batch.append(reading)
                    total += 1
            
            # Sauvegarder par lot
            db.bulk_save_objects(readings_batch)
            db.commit()
            print(f"      → {len(readings_batch)} lectures créées")
        
        print(f"✅ {total:,} lectures créées au total")
        return total
        
    except Exception as e:
        print(f"❌ ERREUR lors de la création des lectures:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 0


def verify_data(db: Session):
    """Vérifie que les données ont bien été créées"""
    print("\n✅ ÉTAPE 7 : Vérification finale...")
    
    try:
        count_sites = db.query(Site).count()
        count_meters = db.query(Meter).count()
        count_readings = db.query(ConsumptionReading).count()
        
        print(f"   • Sites: {count_sites}")
        print(f"   • Compteurs: {count_meters}")
        print(f"   • Lectures: {count_readings:,}")
        
        if count_sites > 0 and count_meters > 0 and count_readings > 0:
            print("\n✅ Toutes les données ont été créées avec succès!")
            return True
        else:
            print("\n⚠️  Certaines données manquent")
            return False
            
    except Exception as e:
        print(f"❌ ERREUR lors de la vérification:")
        print(f"   {e}")
        return False


def main():
    """Fonction principale"""
    print("=" * 60)
    print("🌱 SEED DE LA BASE DE DONNÉES (VERSION DEBUG)")
    print("=" * 60)
    
    # Vérifications préalables
    if not check_database_connection():
        sys.exit(1)
    
    if not check_tables_exist():
        sys.exit(1)
    
    # Créer une session
    db = SessionLocal()
    
    try:
        # Nettoyer
        if not clear_existing_data(db):
            sys.exit(1)
        
        # Créer les données
        sites = create_sites(db)
        if not sites:
            print("\n❌ Échec de la création des sites")
            sys.exit(1)
        
        meters = create_meters(db, sites)
        if not meters:
            print("\n❌ Échec de la création des compteurs")
            sys.exit(1)
        
        total_readings = create_readings(db, meters, days=7)
        if total_readings == 0:
            print("\n❌ Échec de la création des lectures")
            sys.exit(1)
        
        # Vérifier
        verify_data(db)
        
        print("\n" + "=" * 60)
        print("✅ SEED TERMINÉ AVEC SUCCÈS!")
        print("=" * 60)
        print("\n💡 Prochaines étapes:")
        print("   1. Lancer l'API: uvicorn app.main:app --reload")
        print("   2. Tester: http://localhost:8000/docs")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERREUR GLOBALE: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
        
    finally:
        db.close()


if __name__ == "__main__":
    main()