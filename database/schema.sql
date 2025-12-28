CREATE TABLE IF NOT EXISTS dipendenti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cognome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    data_assunzione DATE NOT NULL,
    colore TEXT DEFAULT '#4361ee'
);

CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'viewer' CHECK(role IN ('viewer', 'admin'))
);

CREATE TABLE IF NOT EXISTS timbrature (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dipendente_id INTEGER NOT NULL,
    inizio DATETIME NOT NULL,
    fine DATETIME,
    note TEXT,
    FOREIGN KEY (dipendente_id) REFERENCES dipendenti(id)
);

-- Utente Dashboard (sola visualizzazione report)
INSERT OR IGNORE INTO admin (username, password, role) 
VALUES ('dashboard', 'dashboard', 'viewer');

-- Utente Admin (accesso completo)
INSERT OR IGNORE INTO admin (username, password, role) 
VALUES ('admin', 'admin', 'admin');