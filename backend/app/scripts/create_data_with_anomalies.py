"""
Script pour créer des données avec BEAUCOUP d'anomalies visibles
"""

from datetime import datetime, timedelta
import random
import numpy as np

# IMPORTANT: Ordre des imports
from app.core.database import Base, SessionLocal

# Tous les modèles
from app.models.site import Site
from app.models.meter import Meter
from app.models.consumption import ConsumptionReading

def create_data_with_anomalies():
    """Crée des données avec anomalies évidentes"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("🎲 CRÉATION DE DONNÉES AVEC ANOMALIES")
        print("=" * 60)
        
        # Supprimer les anciennes lectures
        deleted = db.query(ConsumptionReading).delete()
        print(f"\n🗑️  {deleted} anciennes lectures supprimées")
        
        # Créer des lectures pour les 7 derniers jours
        base_time = datetime.utcnow() - timedelta(days=7)
        
        total_readings = 0
        total_anomalies = 0
        
        for meter_id in range(1, 11):  # Compteurs 1 à 10
            print(f"\n📟 Compteur {meter_id}...")
            
            readings = []
            anomaly_count = 0
            
            for day in range(7):
                for hour in range(24):
                    timestamp = base_time + timedelta(days=day, hours=hour)
                    
                    # Valeur normale : entre 80 et 140 kWh
                    base_value = 100.0 + (hour * 2)  # Pattern journalier
                    noise = random.uniform(-10, 10)
                    normal_value = base_value + noise
                    
                    # Injecter des anomalies (~10% des données)
                    if random.random() < 0.10:  # 10% de chance
                        # Anomalie = valeur × 2 ou ÷ 2
                        if random.random() < 0.5:
                            value = normal_value * random.uniform(2.5, 3.5)  # Pic élevé
                        else:
                            value = normal_value / random.uniform(2.5, 3.5)  # Chute brutale
                        anomaly_count += 1
                    else:
                        value = normal_value
                    
                    reading = ConsumptionReading(
                        meter_id=meter_id,
                        timestamp=timestamp,
                        value_kwh=max(0, value)  # Pas de valeurs négatives
                    )
                    readings.append(reading)
            
            # Sauvegarder
            db.bulk_save_objects(readings)
            db.commit()
            
            total_readings += len(readings)
            total_anomalies += anomaly_count
            
            print(f"   ✓ {len(readings)} lectures créées")
            print(f"   🔴 ~{anomaly_count} anomalies injectées (non détectées)")
        
        print("\n" + "=" * 60)
        print(f"✅ CRÉATION TERMINÉE")
        print(f"   📊 Total lectures : {total_readings}")
        print(f"   🔴 Anomalies injectées : ~{total_anomalies}")
        print("=" * 60)
        print("\n💡 Prochaine étape : Lancer la détection")
        print("   python detect_anomalies.py")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_data_with_anomalies()