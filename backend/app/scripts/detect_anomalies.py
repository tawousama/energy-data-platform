"""
Script de détection d'anomalies avec debug complet
"""

# IMPORTANT: Importer Base en premier pour initialiser SQLAlchemy
from app.core.database import Base, SessionLocal

# Puis importer tous les modèles pour les enregistrer
from app.models.site import Site
from app.models.meter import Meter
from app.models.consumption import ConsumptionReading

# Puis le service
from app.services.anomaly_detection import AnomalyDetectionService

from datetime import datetime, timedelta

def detect_with_debug():
    """Détecte les anomalies avec logs détaillés"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("🔍 DÉTECTION D'ANOMALIES (MODE DEBUG)")
        print("=" * 60)
        
        # 1. Vérifier les compteurs
        meters = db.query(Meter).all()
        print(f"\n📊 Compteurs disponibles : {len(meters)}")
        
        if len(meters) == 0:
            print("❌ Aucun compteur trouvé !")
            print("   Lancez d'abord : python create_data_with_anomalies.py")
            return
        
        # 2. Vérifier les lectures
        total_readings = db.query(ConsumptionReading).count()
        print(f"📊 Lectures totales : {total_readings}")
        
        if total_readings == 0:
            print("❌ Aucune lecture trouvée !")
            print("   Lancez d'abord : python create_data_with_anomalies.py")
            return
        
        # 3. Tester sur le compteur 1
        meter_id = 1
        print(f"\n🎯 Test sur le compteur {meter_id}...")
        
        # Vérifier les données du compteur 1
        readings = db.query(ConsumptionReading).filter(
            ConsumptionReading.meter_id == meter_id
        ).all()
        
        print(f"   📊 Lectures du compteur {meter_id} : {len(readings)}")
        
        if len(readings) < 10:
            print("   ❌ Pas assez de données pour détecter des anomalies")
            return
        
        # Afficher un échantillon des valeurs
        values = [r.value_kwh for r in readings[:20]]
        print(f"   📈 Échantillon de valeurs : {[round(v, 2) for v in values[:5]]}")
        print(f"   📊 Min: {min(values):.2f}, Max: {max(values):.2f}, Moy: {sum(values)/len(values):.2f}")
        
        # 4. Créer le service et détecter
        print(f"\n🔍 Détection avec Z-Score...")
        service = AnomalyDetectionService(db)
        
        # Détecter SANS marquer (pour debug)
        anomalies = service.detect_anomalies_zscore(meter_id)
        print(f"   🔴 Anomalies détectées : {len(anomalies)}")
        
        if len(anomalies) > 0:
            print(f"   📊 Exemples (reading_id, score) :")
            for reading_id, score in anomalies[:5]:
                reading = db.query(ConsumptionReading).filter(
                    ConsumptionReading.id == reading_id
                ).first()
                if reading:
                    print(f"      • Reading #{reading_id} : {reading.value_kwh:.2f} kWh (score: {score:.2f}σ)")
        else:
            print("   ⚠️  Aucune anomalie détectée avec Z-Score")
            print("   💡 Les données sont peut-être trop uniformes")
            print("   💡 Relancez : python create_data_with_anomalies.py")
            return
        
        # 5. MARQUER les anomalies dans la BDD
        print(f"\n✍️  Marquage des anomalies dans la base...")
        count = service.mark_anomalies(meter_id, method="zscore")
        print(f"   ✅ {count} anomalies marquées")
        
        # 6. Vérifier que ça a marché
        print(f"\n🔍 Vérification dans la base...")
        marked = db.query(ConsumptionReading).filter(
            ConsumptionReading.meter_id == meter_id,
            ConsumptionReading.is_anomaly == True
        ).count()
        
        print(f"   📊 Anomalies marquées (is_anomaly=true) : {marked}")
        
        if marked > 0:
            print(f"   ✅ Succès ! Les anomalies sont bien marquées")
            
            # Afficher quelques exemples
            examples = db.query(ConsumptionReading).filter(
                ConsumptionReading.meter_id == meter_id,
                ConsumptionReading.is_anomaly == True
            ).limit(3).all()
            
            print(f"\n   📋 Exemples d'anomalies :")
            for ex in examples:
                print(f"      • {ex.timestamp.strftime('%Y-%m-%d %H:%M')} : {ex.value_kwh:.2f} kWh (score: {ex.anomaly_score:.2f}σ, status: {ex.anomaly_status})")
        else:
            print(f"   ❌ PROBLÈME : Les anomalies ne sont pas marquées !")
            print(f"   💡 Vérifiez que la colonne 'is_anomaly' existe")
            print(f"   💡 Lancez : python migrate_add_status.py")
        
        # 7. Détecter sur TOUS les compteurs
        print(f"\n🚀 Détection sur tous les compteurs...")
        total_anomalies = 0
        
        for meter in meters:
            count = service.mark_anomalies(meter.id, method="zscore")
            total_anomalies += count
            if count > 0:
                print(f"   📟 Compteur {meter.id} : {count} anomalies")
        
        print(f"\n" + "=" * 60)
        print(f"✅ TOTAL : {total_anomalies} anomalies détectées")
        print("=" * 60)
        
        # Vérification finale globale
        total_marked = db.query(ConsumptionReading).filter(
            ConsumptionReading.is_anomaly == True
        ).count()
        
        print(f"\n🔍 Vérification finale :")
        print(f"   📊 Total lectures : {total_readings}")
        print(f"   🔴 Total anomalies : {total_marked}")
        print(f"   📈 Taux : {(total_marked / total_readings * 100):.2f}%")
        
        if total_marked > 0:
            print(f"\n✅ Succès ! Allez voir dans le frontend :")
            print(f"   http://localhost:5173/analytics")
        else:
            print(f"\n❌ Aucune anomalie marquée. Problèmes possibles :")
            print(f"   1. Colonne 'is_anomaly' manquante → python migrate_add_status.py")
            print(f"   2. Données trop uniformes → python create_data_with_anomalies.py")
        
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    detect_with_debug()