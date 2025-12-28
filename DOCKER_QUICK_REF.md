# 🐳 Docker Quick Reference

## Credenziali Default

### Dashboard (Visualizzazione)
```
Username: dashboard
Password: dashboard
```

### Admin (Gestione Completa)
```
Username: admin
Password: admin
```
⚠️ Cambia dopo il primo accesso!

## Comandi Essenziali

### Avvio
```bash
docker-compose up -d
```

### Stato e Logs
```bash
docker-compose ps              # Stato container + healthcheck
docker-compose logs -f         # Logs in tempo reale
```

### Stop e Restart
```bash
docker-compose stop            # Ferma
docker-compose restart         # Riavvia
docker-compose down            # Ferma e rimuovi container
```

### Accesso
- **App**: http://localhost:5003
- **Login**: http://localhost:5003/login
- **Admin**: http://localhost:5003/admin

### Backup Database
```bash
cp data/timbrature.db data/backup_$(date +%Y%m%d).db
```

### Reset Completo
```bash
docker-compose down -v
rm -rf data/
docker-compose up -d
```

## Healthcheck
Usa `wget` ogni 30s:
```bash
wget --quiet --tries=1 --spider http://localhost:5000/
```

## Troubleshooting
```bash
# Rebuild da zero
docker-compose build --no-cache

# Verifica permessi
chmod 755 data/

# Logs dettagliati
docker-compose logs --tail=100
```

📖 Documentazione completa: [DOCKER.md](DOCKER.md)
