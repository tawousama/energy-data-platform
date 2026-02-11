"""
Script ALL-IN-ONE : Crée les données ET détecte les anomalies
"""

from datetime import datetime, timedelta
import random

# Imports dans le bon ordre
from app.core.database import Base, SessionLocal

# Tous les modèles
from app.models.site import Site
from app.models.meter import Meter  
from app.models.consumption import ConsumptionReading

# Service
from app.services.anomaly_detection import AnomalyDetectionService


def all_in_one():
    """Crée les données et détecte les anomalies en une seule fois"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("🚀 SCRIPT ALL-IN-ONE")
        print("=" * 60)
        
        # === PARTIE 1 : CRÉER LES DONNÉES ===
        print("\n📊 PARTIE 1 : Création des données avec anomalies")
        print("-" * 60)
        
        # Supprimer les anciennes lectures
        deleted = db.query(ConsumptionReading).delete()
        db.commit()
        print(f"🗑️  {deleted} anciennes lectures supprimées")
        
        # Créer des lectures pour les 7 derniers jours
        base_time = datetime.utcnow() - timedelta(days=7)
        
        total_readings = 0
        
        for meter_id in range(1, 11):  # Compteurs 1 à 10
            readings = []
            
            for day in range(7):
                for hour in range(24):
                    timestamp = base_time + timedelta(days=day, hours=hour)
                    
                    # Valeur normale
                    base_value = 100.0 + (hour * 2)
                    noise = random.uniform(-10, 10)
                    normal_value = base_value + noise
                    
                    # Injecter des anomalies (10%)
                    if random.random() < 0.10:
                        if random.random() < 0.5:
                            value = normal_value * random.uniform(2.5, 3.5)
                        else:
                            value = normal_value / random.uniform(2.5, 3.5)
                    else:
                        value = normal_value
                    
                    reading = ConsumptionReading(
                        meter_id=meter_id,
                        timestamp=timestamp,
                        value_kwh=max(0, value),
                        anomaly_status='pending'  # Initialiser le statut
                    )
                    readings.append(reading)
            
            db.bulk_save_objects(readings)
            db.commit()
            total_readings += len(readings)
            print(f"✓ Compteur {meter_id} : {len(readings)} lectures créées")
        
        print(f"\n✅ {total_readings} lectures créées au total")
        
        # === PARTIE 2 : DÉTECTER LES ANOMALIES ===
        print("\n🔍 PARTIE 2 : Détection des anomalies")
        print("-" * 60)
        
        service = AnomalyDetectionService(db)
        total_anomalies = 0
        
        for meter_id in range(1, 11):
            count = service.mark_anomalies(meter_id, method="zscore")
            total_anomalies += count
            if count > 0:
                print(f"🔴 Compteur {meter_id} : {count} anomalies détectées")
        
        print(f"\n✅ {total_anomalies} anomalies détectées au total")
        
        # === PARTIE 3 : VÉRIFICATION ===
        print("\n✅ PARTIE 3 : Vérification finale")
        print("-" * 60)
        
        total = db.query(ConsumptionReading).count()
        anomalies = db.query(ConsumptionReading).filter(
            ConsumptionReading.is_anomaly == True
        ).count()
        
        print(f"📊 Total lectures : {total}")
        print(f"🔴 Total anomalies : {anomalies}")
        print(f"📈 Taux : {(anomalies / total * 100):.2f}%")
        
        # Afficher quelques exemples
        print(f"\n📋 Exemples d'anomalies :")
        examples = db.query(ConsumptionReading).filter(
            ConsumptionReading.is_anomaly == True
        ).limit(5).all()
        
        for ex in examples:
            print(f"   • Compteur {ex.meter_id} : {ex.value_kwh:.2f} kWh (score: {ex.anomaly_score:.2f}σ)")
        
        print("\n" + "=" * 60)
        print("✅ TERMINÉ ! Allez voir le frontend :")
        print("   http://localhost:5173/analytics")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    all_in_one()