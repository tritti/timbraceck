import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'timbrature.db')

def add_column():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE dipendenti ADD COLUMN colore TEXT DEFAULT '#4361ee'")
        conn.commit()
        print("Column 'colore' added successfully.")
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_column()
