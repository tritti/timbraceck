# Sistema Gestione Timbrature

Applicazione web per la gestione delle timbrature dei dipendenti, realizzata con Python, Flask, JavaScript e SQLite.

## Caratteristiche

- Dashboard per le timbrature dei dipendenti (entrata/uscita)
- Area amministrativa protetta da login
- Gestione completa dei dipendenti (aggiunta, modifica, eliminazione)
- Report dettagliati delle ore lavorate
- Grafici e statistiche
- Interfaccia responsive

## Requisiti

- Python 3.7+
- Flask
- SQLite

## Installazione

1. Clona il repository:

```bash
git clone https://github.com/yourusername/timbrature.git
cd timbrature
```

2. Crea un ambiente virtuale e attivalo:

```bash
python -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate
```

3. Installa le dipendenze:

```bash
pip install Flask Werkzeug
```

4. Avvia l'applicazione:

```bash
python app.py
```

5. Apri il browser e vai a `http://localhost:5000`

## Utilizzo

### Area Dipendenti

- Nella homepage, ciascun dipendente può registrare la propria entrata o uscita cliccando sulla propria card
- Il sistema registra automaticamente l'orario di timbratura

### Area Amministrativa

- Accedi all'area admin da `/login` o dal link "Area Admin" nel menu
- Credenziali di default: username `admin`, password `admin`
- Da qui puoi:
  - Gestire i dipendenti (aggiungere, modificare, eliminare)
  - Visualizzare i report delle ore lavorate
  - Analizzare le statistiche di presenza

## Struttura del Progetto

```
/timbrature/
│
├── app.py                 # Applicazione Flask principale
├── database/
│   ├── schema.sql         # Schema del database
│   └── timbrature.db      # Database SQLite
├── static/
│   ├── css/
│   │   └── style.css      # Stili CSS personalizzati
│   └── js/
│       └── timbrature.js  # JavaScript per la pagina delle timbrature
└── templates/
    ├── base.html          # Template base
    ├── index.html         # Homepage (timbrature)
    ├── login.html         # Pagina di login
    └── admin/
        ├── dashboard.html        # Dashboard admin
        ├── dipendenti.html       # Gestione dipendenti
        ├── dipendente_edit.html  # Modifica dipendente
        └── report.html           # Pagina dei report
```

## Note di Sicurezza

- La password dell'admin è hashata nel database
- Le rotte amministrative sono protette da autenticazione
- Per un ambiente di produzione, generare una nuova SECRET_KEY