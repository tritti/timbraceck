# Timbraceck

Applicazione web per la gestione delle timbrature dei dipendenti, realizzata con Python, Flask, JavaScript e **Neon (PostgreSQL)**.

## Caratteristiche

- Dashboard per le timbrature dei dipendenti (entrata/uscita)
- Area amministrativa protetta da login
- Gestione completa dei dipendenti (aggiunta, modifica, eliminazione)
- Report dettagliati delle ore lavorate
- Grafici e statistiche
- Interfaccia responsive

## Requisiti

- Python 3.10+
- Flask
- PostgreSQL (Neon)

## Installazione

1. Clona il repository:

```bash
git clone https://github.com/tritti/timbraceck.git
cd timbraceck
```

2. Crea un ambiente virtuale e attivalo:

```bash
python3 -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate
```

3. Installa le dipendenze:

```bash
pip install -r requirements.txt
```

4. Configurazione Database:

Crea un file `.env` nella root del progetto:

```bash
FLASK_ENV=development
# Sostituisci con la tua stringa di connessione Neon (Dev o Prod)
DATABASE_URL=postgresql://user:password@endpoint.neon.tech/neondb
SECRET_KEY=tua-chiave-segreta-random
```

5. Avvia l'applicazione:

```bash
flask run --port 5003
```

6. Apri il browser e vai a `http://localhost:5003`

## Utilizzo

### Area Dipendenti

- Nella homepage, ciascun dipendente può registrare la propria entrata o uscita cliccando sulla propria card
- Il sistema registra automaticamente l'orario di timbratura

### Area Amministrativa

- Accedi all'area admin da `/login`
- **Nota**: Al primo accesso, verrà richiesto di cambiare la password di default.

### Struttura del Progetto

```
/timbraceck/
│
├── app.py                 # Applicazione Flask principale
├── db_wrapper.py          # Wrapper per compatibilità Postgres
├── database/
│   ├── schema_pg.sql      # Schema PostgreSQL
│   └── timbrature.db      # (Legacy) Database SQLite
├── static/
├── templates/
└── .env                   # Configurazione ambiente (non committato)
```