"""
Migration : Ajouter anomaly_status à consumption_readings
"""

import psycopg2

def migrate():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="energy_user",
            password="energy_password",
            database="energy_db"
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("🔧 Migration : Ajout du champ anomaly_status...")
        
        # Vérifier si la colonne existe déjà
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='consumption_readings' 
            AND column_name='anomaly_status'
        """)
        
        if cursor.fetchone():
            print("✅ La colonne anomaly_status existe déjà")
        else:
            # Ajouter la colonne
            cursor.execute("""
                ALTER TABLE consumption_readings 
                ADD COLUMN anomaly_status VARCHAR(20) DEFAULT 'pending'
            """)
            print("✅ Colonne anomaly_status ajoutée")
            
            # Créer un index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS ix_anomaly_status 
                ON consumption_readings(anomaly_status)
            """)
            print("✅ Index créé sur anomaly_status")
        
        cursor.close()
        conn.close()
        print("\n✅ Migration terminée avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    migrate()