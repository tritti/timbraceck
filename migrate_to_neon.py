import sqlite3
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
SQLITE_DB_PATH = os.path.join('database', 'timbrature.db')
POSTGRES_DB_URL = os.getenv('DATABASE_URL')

def migrate():
    print("Starting migration from SQLite to Neon Postgres...")
    
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"Error: SQLite database not found at {SQLITE_DB_PATH}")
        return

    if not POSTGRES_DB_URL:
        print("Error: DATABASE_URL not found in environment")
        return

    # Connect to SQLite
    print("Connecting to SQLite...")
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    # Connect to Postgres
    print("Connecting to Neon Postgres...")
    pg_conn = psycopg2.connect(POSTGRES_DB_URL)
    pg_cur = pg_conn.cursor()

    try:
        # 1. Initialize Schema in Postgres
        print("Initializing Postgres schema...")
        with open(os.path.join('database', 'schema_pg.sql'), 'r') as f:
            pg_cur.execute(f.read())
        pg_conn.commit()

        # 2. Clear existing data in Postgres (optional, for safety during dev)
        print("Clearing existing data in target...")
        pg_cur.execute("TRUNCATE TABLE timbrature, dipendenti, admin CASCADE;")

        # 3. Migrate Admin Users
        print("Migrating Admin/Users...")
        sqlite_cur.execute("SELECT * FROM admin")
        admins = sqlite_cur.fetchall()
        for admin in admins:
            pg_cur.execute(
                "INSERT INTO admin (username, password, role) VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING",
                (admin['username'], admin['password'], admin['role'])
            )
        
        # 4. Migrate Dipendenti
        print("Migrating Dipendenti...")
        sqlite_cur.execute("SELECT * FROM dipendenti")
        dipendenti = sqlite_cur.fetchall()
        # Maintain ID mapping if necessary, but here we can just insert with explicit IDs
        for d in dipendenti:
            pg_cur.execute(
                """INSERT INTO dipendenti (id, nome, cognome, email, data_assunzione, colore) 
                   VALUES (%s, %s, %s, %s, %s, %s) 
                   ON CONFLICT (id) DO UPDATE SET email=EXCLUDED.email""",
                (d['id'], d['nome'], d['cognome'], d['email'], d['data_assunzione'], d['colore'])
            )
            # Update sequence for dipendenti_id
        
        # Reset sequence for dipendenti
        pg_cur.execute("SELECT setval('dipendenti_id_seq', (SELECT MAX(id) FROM dipendenti))")

        # 5. Migrate Timbrature
        print("Migrating Timbrature...")
        sqlite_cur.execute("SELECT * FROM timbrature")
        timbrature = sqlite_cur.fetchall()
        for t in timbrature:
            pg_cur.execute(
                """INSERT INTO timbrature (dipendente_id, inizio, fine, note) 
                   VALUES (%s, %s, %s, %s)""",
                (t['dipendente_id'], t['inizio'], t['fine'], t['note'] if 'note' in t.keys() else None)
            )
            
        pg_conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")
        pg_conn.rollback()
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
