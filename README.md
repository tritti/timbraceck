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

- Docker & Docker Compose
- Account Neon (PostgreSQL)

## Installazione (Docker)

1. Clona il repository:

```bash
git clone https://github.com/tritti/timbraceck.git
cd timbraceck
```

2. Configurazione:

Copia il file di esempio per creare la tua configurazione:

```bash
cp .env.example .env
```

Modifica il file `.env` inserendo la tua stringa di connessione Neon e una Secret Key sicura.

3. Avvia l'applicazione con Docker:

```bash
docker compose up --build
```

4. Apri il browser e vai a `http://localhost:5003`

---

## Installazione Manuale (Senza Docker)

1. Crea e attiva virtualenv: `python3 -m venv venv` && `source venv/bin/activate`
2. Installa dipendenze: `pip install -r requirements.txt`
3. Configura `.env` (vedi sopra)
4. Avvia: `flask run --port 5003`

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
├── Dockerfile             # Configurazione Docker
├── docker-compose.yml     # Orchestrazione servizi
└── .env                   # Configurazione ambiente (non committato)
```