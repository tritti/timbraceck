import os
import sqlite3
import random
import datetime
from datetime import timedelta, date, datetime

# Path al database
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'timbrature.db')

# Funzione per ottenere una connessione al database
def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

# Funzione per generare una data casuale tra inizio e fine
def random_date(start_date, end_date):
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

# Crea dipendenti di test
def create_test_employees():
    print("Creazione dipendenti di test...")
    
    dipendenti = [
        ("Mario", "Rossi", "mario.rossi@example.com", "2023-01-15"),
        ("Giulia", "Bianchi", "giulia.bianchi@example.com", "2023-02-01"),
        ("Paolo", "Verdi", "paolo.verdi@example.com", "2023-03-10"),
        ("Francesca", "Ferrari", "francesca.ferrari@example.com", "2023-04-05"),
        ("Alessandro", "Ricci", "alessandro.ricci@example.com", "2022-11-20"),
        ("Laura", "Marini", "laura.marini@example.com", "2022-10-15")
    ]
    
    db = get_db()
    
    # Pulisci le tabelle esistenti
    print("Pulizia delle tabelle esistenti...")
    db.execute("DELETE FROM timbrature")
    db.execute("DELETE FROM dipendenti")
    db.commit()
    
    # Inserisci i dipendenti
    for dipendente in dipendenti:
        try:
            db.execute(
                "INSERT INTO dipendenti (nome, cognome, email, data_assunzione) VALUES (?, ?, ?, ?)",
                dipendente
            )
        except sqlite3.IntegrityError:
            print(f"Errore: email {dipendente[2]} già in uso.")
    
    db.commit()
    print(f"Creati {len(dipendenti)} dipendenti.")
    
    return [row['id'] for row in db.execute("SELECT id FROM dipendenti").fetchall()]

# Genera timbrature casuali per i dipendenti
def create_random_timbrature(dipendente_ids):
    print("Generazione timbrature casuali...")
    db = get_db()
    
    # Data di inizio e fine (ultimo anno)
    end_date = datetime.now()
    start_date = datetime(end_date.year -2, end_date.month, end_date.day)
    
    # Numero medio di giorni lavorati al mese per dipendente
    work_days_per_month = 20
    
    total_entries = 0
    
    for dipendente_id in dipendente_ids:
        # Genera date casuali per l'anno
        current_date = start_date
        
        while current_date < end_date:
            # Per ogni mese, genera circa 20 giorni lavorativi
            month_start = current_date.replace(day=1)
            month_end = (month_start.replace(month=month_start.month+1) if month_start.month < 12 
                        else month_start.replace(year=month_start.year+1, month=1))
            month_end = min(month_end, end_date)
            
            # Giorni in cui il dipendente ha lavorato questo mese
            work_days = min(work_days_per_month, (month_end - month_start).days)
            
            # Genera le date di lavoro per questo mese
            work_dates = sorted(random.sample(range(1, (month_end - month_start).days + 1), work_days))
            
            for day in work_dates:
                work_date = month_start + timedelta(days=day-1)
                
                # Ora di inizio (tra le 8:00 e le 10:00)
                start_hour = random.randint(8, 10)
                start_minute = random.randint(0, 59)
                inizio = datetime(work_date.year, work_date.month, work_date.day, 
                                 start_hour, start_minute, 0)
                
                # Ore lavorate (tra 3 e 12 ore)
                ore_lavorate = random.uniform(3.0, 12.0)
                
                # Ora di fine
                fine = inizio + timedelta(hours=ore_lavorate)
                
                # Inserisci la timbratura
                db.execute(
                    "INSERT INTO timbrature (dipendente_id, inizio, fine) VALUES (?, ?, ?)",
                    (dipendente_id, inizio.strftime('%Y-%m-%d %H:%M:%S'), fine.strftime('%Y-%m-%d %H:%M:%S'))
                )
                total_entries += 1
            
            # Passa al mese successivo
            current_date = month_end
    
    db.commit()
    print(f"Create {total_entries} timbrature casuali.")

# Funzione principale
def main():
    print(f"Popolo il database {DB_PATH} con dati di test...")
    
    # Verifica che il database esista
    if not os.path.exists(DB_PATH):
        print(f"ERRORE: Il database {DB_PATH} non esiste.")
        print("Esegui prima l'app Python per creare il database.")
        return
    
    # Crea i dipendenti e ottieni i loro ID
    dipendente_ids = create_test_employees()
    
    # Genera timbrature casuali
    create_random_timbrature(dipendente_ids)
    
    print("Popolazione completata con successo!")

if __name__ == "__main__":
    main()