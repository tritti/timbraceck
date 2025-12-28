# Docker Setup per Timbrature

Questa applicazione Flask per la gestione delle timbrature è ora containerizzata con Docker.

## 🔐 Credenziali di Default

**IMPORTANTE**: Al primo avvio, l'applicazione ha due utenti con permessi diversi:

### Utente Dashboard (Visualizzazione)
- **Username**: `dashboard`
- **Password**: `dashboard`
- **Permessi**: Solo visualizzazione report e timbrature

### Utente Admin (Gestione Completa)
- **Username**: `admin`
- **Password**: `admin`
- **Permessi**: Accesso completo (gestione dipendenti, modifica timbrature, ecc.)

> ⚠️ **Sicurezza**: Cambia entrambe le password immediatamente dopo il primo accesso in produzione!

Le password vengono automaticamente convertite in formato hash al primo login.

## 🚀 Avvio Rapido

### Prerequisiti
- Docker
- Docker Compose

### Comandi Base

```bash
# Build e avvio dell'applicazione
docker-compose up -d

# Visualizza i log
docker-compose logs -f

# Verifica lo stato (include healthcheck)
docker-compose ps

# Ferma l'applicazione
docker-compose down

# Ferma e rimuovi i volumi (ATTENZIONE: cancella il database!)
docker-compose down -v
```

## 📁 Struttura

```
timbrature-main/
├── Dockerfile              # Configurazione immagine Docker
├── docker-compose.yml      # Orchestrazione container
├── entrypoint.sh          # Script di inizializzazione
├── .dockerignore          # File esclusi dal build
├── data/                  # Volume persistente per database
│   └── timbrature.db      # Database SQLite (creato automaticamente)
├── app.py                 # Applicazione Flask principale
├── init_db.py            # Script inizializzazione database
├── requirements.txt       # Dipendenze Python
└── ...
```

## 🏥 Healthcheck

L'applicazione include un healthcheck basato su `wget` che verifica ogni 30 secondi che il servizio sia attivo:

```yaml
healthcheck:
  test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:5003/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## 🔧 Configurazione

### Variabili d'Ambiente

Puoi personalizzare la configurazione modificando `docker-compose.yml`:

```yaml
environment:
  - FLASK_ENV=production
  - DATABASE_PATH=/app/data/timbrature.db
```

### Porte

L'applicazione è esposta sulla porta `5003`. Per cambiarla, modifica in `docker-compose.yml`:

```yaml
ports:
  - "8080:5003"  # Usa porta 8080 invece di 5003
```

## 💾 Persistenza Dati

Il database è salvato in un volume Docker mappato sulla cartella `./data` dell'host. I dati persistono anche dopo il riavvio o la rimozione del container.

Per fare un backup:
```bash
# Copia il database
cp data/timbrature.db data/timbrature.db.backup

# Oppure usa docker cp
docker cp timbrature-flask:/app/data/timbrature.db ./backup.db
```

## 🐛 Troubleshooting

### Il container non si avvia
```bash
# Controlla i log
docker-compose logs

# Ricostruisci l'immagine
docker-compose build --no-cache
docker-compose up -d
```

### Problemi di permessi sul database
```bash
# Assicurati che la directory data esista e sia scrivibile
mkdir -p data
chmod 755 data
```

### Reset completo
```bash
# Ferma tutto e rimuovi volumi
docker-compose down -v

# Rimuovi la directory data
rm -rf data/

# Riavvia
docker-compose up -d
```

## 📊 Accesso all'Applicazione

Dopo l'avvio, accedi a:
- **URL**: http://localhost:5003
- **Login**: http://localhost:5003/login
- **Admin Dashboard**: http://localhost:5003/admin

## 🔒 Sicurezza

1. **Cambia la password di default** dopo il primo accesso
2. Il container gira con un utente non-root (`appuser`)
3. Usa `gunicorn` come server WSGI production-ready
4. Il database è isolato nel container con volume persistente

## 📝 Note di Produzione

Per un deployment in produzione, considera:
- Usare un reverse proxy (nginx/traefik) con HTTPS
- Configurare backup automatici del database
- Impostare limiti di risorse per il container
- Usare secrets per le credenziali invece di variabili d'ambiente
- Implementare un sistema di logging centralizzato
