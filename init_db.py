import os
import sqlite3

def init_db():
    # Use environment variable if set (for Docker), otherwise use default path
    db_path = os.environ.get('DATABASE_PATH', os.environ.get('DATABASE', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'timbrature.db')))
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'schema.sql')
    
    # Assicurati che la directory database esista
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
    
    # Rimuovi il database esistente se presente
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Database esistente rimosso: {db_path}")
    
    # Crea un nuovo database
    conn = sqlite3.connect(db_path)
    print(f"Nuovo database creato: {db_path}")
    
    # Esegui lo schema SQL
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
        conn.executescript(schema_sql)
    
    # Commit e chiudi
    conn.commit()
    conn.close()
    
    print("Database inizializzato con successo!")

if __name__ == "__main__":
    init_db()
    print("Puoi ora avviare l'applicazione con 'python app.py'")