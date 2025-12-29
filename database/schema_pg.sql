-- Postgres Schema for Timbraceck

CREATE TABLE IF NOT EXISTS dipendenti (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    cognome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    data_assunzione DATE NOT NULL,
    colore TEXT DEFAULT '#4361ee'
);

CREATE TABLE IF NOT EXISTS admin (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'viewer' CHECK(role IN ('viewer', 'admin', 'dipendente'))
);

CREATE TABLE IF NOT EXISTS timbrature (
    id SERIAL PRIMARY KEY,
    dipendente_id INTEGER NOT NULL REFERENCES dipendenti(id) ON DELETE CASCADE,
    inizio TIMESTAMP NOT NULL,
    fine TIMESTAMP,
    note TEXT
);

-- Indexes for performance (optional but good practice)
CREATE INDEX IF NOT EXISTS idx_timbrature_dipendente ON timbrature(dipendente_id);
CREATE INDEX IF NOT EXISTS idx_timbrature_inizio ON timbrature(inizio);

-- Initial Users (using ON CONFLICT to avoid errors on re-run)
INSERT INTO admin (username, password, role) 
VALUES ('dashboard', 'dashboard', 'viewer')
ON CONFLICT (username) DO NOTHING;

INSERT INTO admin (username, password, role) 
VALUES ('admin', 'admin', 'admin')
ON CONFLICT (username) DO NOTHING;
