import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'timbrature.db')

def migrate_db():
    print(f"Migrazione database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 1. Rinomina tabella esistente
        print("1. Rinomina tabella admin esistente...")
        cursor.execute("ALTER TABLE admin RENAME TO admin_old")

        # 2. Crea nuova tabella con vincolo aggiornato
        print("2. Creazione nuova tabella admin con ruolo 'dipendente'...")
        cursor.execute("""
            CREATE TABLE admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer' CHECK(role IN ('viewer', 'admin', 'dipendente'))
            )
        """)

        # 3. Copia i dati
        print("3. Copia dei dati esistenti...")
        cursor.execute("INSERT INTO admin (id, username, password, role) SELECT id, username, password, role FROM admin_old")

        # 4. Elimina tabella vecchia
        print("4. Pulizia vecchia tabella...")
        cursor.execute("DROP TABLE admin_old")

        # 5. Inserisci utente default dipendenti
        print("5. Inserimento utente 'dipendenti'...")
        cursor.execute("INSERT OR IGNORE INTO admin (username, password, role) VALUES ('dipendenti', 'dipendenti', 'dipendente')")
        
        conn.commit()
        print("Migrazione completata con successo!")

    except Exception as e:
        conn.rollback()
        print(f"Errore durante la migrazione: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
