from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()

def reset_passwords():
    url = os.environ.get('DATABASE_URL')
    if not url:
        print("DATABASE_URL not found")
        return

    conn = psycopg2.connect(url)
    cur = conn.cursor()

    try:
        # 1. Add column if not exists
        print("Adding force_change column...")
        cur.execute("ALTER TABLE admin ADD COLUMN IF NOT EXISTS force_change BOOLEAN DEFAULT FALSE;")
        
        # 2. Reset passwords and set force_change
        print("Resetting passwords...")
        # Note: We are setting plain text 'temp1234'. 
        # The app logic (login) detects plain text, hashes it, and helps the user login.
        # But we also set force_change=True, so the app handles the forced update.
        cur.execute("UPDATE admin SET password = 'temp1234', force_change = TRUE;")
        
        conn.commit()
        print("Passwords reset successfully.")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    reset_passwords()
