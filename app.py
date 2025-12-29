import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from dotenv import load_dotenv
from db_wrapper import NeonDB
import psycopg2

load_dotenv()

app = Flask(__name__)
# Use environment variable for secret key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
# Use environment variable for database URL
app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL')

# Aggiunta della variabile 'now' a tutti i template
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

def to_datetime(val, format='%Y-%m-%d %H:%M:%S'):
    if val is None:
        return None
    if isinstance(val, str):
        return datetime.strptime(val, format)
    return val

# Funzioni di utilità per il database
# Funzioni di utilità per il database
def get_db():
    if 'db' not in g:
        try:
            conn = psycopg2.connect(app.config['DATABASE_URL'])
            g.db = NeonDB(conn)
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise e
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    print("Inizializzazione del database...")
    db = get_db()
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'schema_pg.sql'), 'r') as f:
        db.execute(f.read())
    db.commit()
    print("Database inizializzato con successo!")

# Decoratore per proteggere le rotte che richiedono autenticazione
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Accesso negato. Effettua il login.', 'error')
            return redirect(url_for('login'))
        
        # Enforce password change
        if session.get('force_change') and request.endpoint not in ('change_password', 'logout', 'static'):
            return redirect(url_for('change_password'))
            
        return f(*args, **kwargs)
    return decorated_function

# Decoratore per proteggere le rotte che richiedono privilegi admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Accesso negato. Effettua il login.', 'error')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Accesso negato. Privilegi amministratore richiesti.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Rotte principali
@app.route('/')
@login_required
def index():
    # Only employees (or admins viewing as employees) access this
    db = get_db()
    
    # Handle fetching dipendenti for the grid view
    # Note: Logic here might need adjustment if we only show logged in user%s 
    # Original logic showed all employees. Keeping as is.
    cur = db.execute('SELECT * FROM dipendenti ORDER BY cognome, nome')
    dipendenti = cur.fetchall()
    return render_template('index.html', dipendenti=dipendenti)

@app.route('/timbratura', methods=['POST'])
@login_required
def timbratura():
    dipendente_id = request.form.get('dipendente_id')
    db = get_db()
    
    # Verifica se esiste una timbratura di ingresso senza uscita
    cur = db.execute(
        'SELECT * FROM timbrature WHERE dipendente_id = %s AND fine IS NULL ORDER BY inizio DESC LIMIT 1',
        (dipendente_id,)
    )
    ultima_timbratura = cur.fetchone()
    
    if ultima_timbratura:
        # Se esiste, registra l'uscita
        now = datetime.now()
        db.execute(
            'UPDATE timbrature SET fine = %s WHERE id = %s',
            (now, ultima_timbratura['id'])
        )
        messaggio = "Timbratura di uscita registrata"
        tipo = "uscita"
    else:
        # Altrimenti registra un nuovo ingresso
        now = datetime.now()
        db.execute(
            'INSERT INTO timbrature (dipendente_id, inizio) VALUES (%s, %s)',
            (dipendente_id, now)
        )
        messaggio = "Timbratura di ingresso registrata"
        tipo = "ingresso"
    
    db.commit()
    
    return jsonify({
        'success': True, 
        'message': messaggio, 
        'tipo': tipo,
        'timestamp': now.strftime('%d/%m/%Y %H:%M:%S')
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_db()
        cur = db.execute('SELECT * FROM admin WHERE username = %s', (username,))
        user = cur.fetchone()
        
        # Controlla sia password in chiaro (per la prima esecuzione/reset) o hashata
        if user:
            pwd_valid = False
            # Check plain text first (migrazione/reset)
            if user['password'] == password:
                pwd_valid = True
                # Hasha la password per sicurezza futura (anche se poi la cambierà)
                hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
                db.execute('UPDATE admin SET password = %s WHERE id = %s', (hashed_password, user['id']))
                db.commit()
            # Check hash standard
            elif user['password'].startswith('pbkdf2') and check_password_hash(user['password'], password):
                pwd_valid = True
            
            if pwd_valid:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                
                # Check for forced password change
                if user.get('force_change'):
                    session['force_change'] = True
                    return redirect(url_for('change_password'))
                
                # Redirect basato sul ruolo
                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user['role'] == 'dipendente':
                     return redirect(url_for('index'))
                else:  # viewer o altri
                    return redirect(url_for('index'))
        
        flash('Username o password non validi', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin/change-password-dipendenti', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_change_password_dipendenti():
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([new_password, confirm_password]):
            flash('Tutti i campi sono obbligatori', 'error')
            return render_template('admin/change_password_dipendenti.html')
        
        if new_password != confirm_password:
            flash('Le nuove password non corrispondono', 'error')
            return render_template('admin/change_password_dipendenti.html')
        
        if len(new_password) < 4:
            flash('La nuova password deve essere di almeno 4 caratteri', 'error')
            return render_template('admin/change_password_dipendenti.html')
            
        db = get_db()
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        
        # Aggiorna password utente 'dipendenti'
        # Note: 'dipendenti' isn't a user here, we check roles. 
        # Logic matches original but uses Postgres syntax
        db.execute('UPDATE admin SET password = %s, force_change = FALSE WHERE role = %s', (hashed_password, 'dipendente'))
        db.commit()
        
        flash('Password per account Dipendenti aggiornata con successo!', 'success')
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin/change_password_dipendenti.html')

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validazione
        if not all([current_password, new_password, confirm_password]):
            flash('Tutti i campi sono obbligatori', 'error')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('Le nuove password non corrispondono', 'error')
            return render_template('change_password.html')
        
        if len(new_password) < 6:
            flash('La nuova password deve essere di almeno 6 caratteri', 'error')
            return render_template('change_password.html')
        
        # Verifica password corrente
        db = get_db()
        cur = db.execute('SELECT * FROM admin WHERE id = %s', (session['user_id'],))
        user = cur.fetchone()
        
        if not user:
            flash('Utente non trovato', 'error')
            return redirect(url_for('logout'))
        
        # Controlla password corrente
        password_valid = False
        if user['password'].startswith('pbkdf2'):
            password_valid = check_password_hash(user['password'], current_password)
        else:
            password_valid = (user['password'] == current_password)
        
        if not password_valid:
            flash('Password corrente non valida', 'error')
            return render_template('change_password.html')
        
        # Aggiorna password
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.execute('UPDATE admin SET password = %s, force_change = FALSE WHERE id = %s', (hashed_password, session['user_id']))
        db.commit()
        
        session.pop('force_change', None)
        flash('Password cambiata con successo!', 'success')
        
        # Redirect basato sul ruolo
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('index'))
    
    # If forced, show message
    if session.get('force_change'):
        flash('Per sicurezza, devi cambiare la tua password al primo accesso.', 'warning')
        
    return render_template('change_password.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/dipendenti')
@login_required
@admin_required
def admin_dipendenti():
    db = get_db()
    dipendenti = db.execute('SELECT * FROM dipendenti ORDER BY cognome, nome').fetchall()
    # Recupera anche gli utenti "hidden soldier" (ruolo dipendente ma non admin)
    viewer_users = db.execute("SELECT * FROM admin WHERE role = 'dipendente' ORDER BY username").fetchall()
    return render_template('admin/dipendenti.html', dipendenti=dipendenti, viewer_users=viewer_users)

@app.route('/admin/dipendente', methods=['POST'])
@login_required
@admin_required
def admin_dipendente_add():
    is_hidden = request.form.get('is_hidden') == 'on'
    db = get_db()
    
    if is_hidden:
        # Creazione Utente "Hidden Soldier" (Admin table)
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not all([username, password]):
             flash('Username e Password sono obbligatori per il soldato nascosto', 'error')
             return redirect(url_for('admin_dipendenti'))
             
        try:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            db.execute(
                "INSERT INTO admin (username, password, role) VALUES (%s, %s, %s)",
                (username, hashed_password, 'dipendente')
            )
            db.commit()
            flash('Utente "Nascosto" creato con successo', 'success')
        except sqlite3.IntegrityError:
            flash('Username già in uso', 'error')
            
    else:
        # Creazione Dipendente Standard
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')
        email = request.form.get('email')
        data_assunzione = request.form.get('data_assunzione')
        colore = request.form.get('colore', '#4361ee')
        
        if not all([nome, cognome, email, data_assunzione]):
            flash('Tutti i campi sono obbligatori', 'error')
            return redirect(url_for('admin_dipendenti'))
        
        try:
            db.execute(
                'INSERT INTO dipendenti (nome, cognome, email, data_assunzione, colore) VALUES (%s, %s, %s, %s, %s)',
                (nome, cognome, email, data_assunzione, colore)
            )
            db.commit()
            flash('Dipendente aggiunto con successo', 'success')
        except sqlite3.IntegrityError:
            flash('Email già in uso', 'error')
    
    return redirect(url_for('admin_dipendenti'))

@app.route('/admin/user/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def admin_user_delete(id):
    db = get_db()
    db.execute('DELETE FROM admin WHERE id = %s AND role = %s', (id, 'dipendente'))
    db.commit()
    return jsonify({'success': True})

@app.route('/admin/dipendente/<int:id>', methods=['GET', 'POST', 'DELETE'])
@login_required
@admin_required
def admin_dipendente_edit(id):
    db = get_db()
    
    if request.method == 'DELETE':
        db.execute('DELETE FROM dipendenti WHERE id = %s', (id,))
        db.commit()
        return jsonify({'success': True})
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')
        email = request.form.get('email')
        data_assunzione = request.form.get('data_assunzione')
        colore = request.form.get('colore', '#4361ee')
        
        if not all([nome, cognome, email, data_assunzione]):
            flash('Tutti i campi sono obbligatori', 'error')
        else:
            try:
                db.execute(
                    'UPDATE dipendenti SET nome = %s, cognome = %s, email = %s, data_assunzione = %s, colore = %s WHERE id = %s',
                    (nome, cognome, email, data_assunzione, colore, id)
                )
                db.commit()
                flash('Dipendente aggiornato con successo', 'success')
            except sqlite3.IntegrityError:
                flash('Email già in uso', 'error')
        
        return redirect(url_for('admin_dipendenti'))
    
    dipendente = db.execute('SELECT * FROM dipendenti WHERE id = %s', (id,)).fetchone()
    if not dipendente:
        flash('Dipendente non trovato', 'error')
        return redirect(url_for('admin_dipendenti'))
    
    return render_template('admin/dipendente_edit.html', dipendente=dipendente)

@app.route('/admin/report')
@login_required
@admin_required
def admin_report():
    return render_template('admin/report.html')

@app.route('/api/report/totale')
@login_required
@admin_required
def api_report_totale():
    db = get_db()
    periodo = request.args.get('periodo', 'mese')
    selected_year = request.args.get('anno', str(datetime.now().year))
    selected_month = request.args.get('mese', str(datetime.now().month))
    
    if periodo == 'settimana':
        data_inizio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        data_fine = datetime.now().strftime('%Y-%m-%d 23:59:59')
    elif periodo == 'mese':
        data_inizio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        data_fine = datetime.now().strftime('%Y-%m-%d 23:59:59')
    elif periodo == 'mese_specifico':
        # Calcola inizio e fine del mese specifico
        try:
            m = int(selected_month)
            y = int(selected_year)
            data_inizio = f"{y}-{m:02d}-01"
            # Calcola ultimo giorno del mese
            if m == 12:
                data_fine = f"{y}-12-31 23:59:59"
            else:
                next_month = datetime(y, m + 1, 1)
                last_day = next_month - timedelta(days=1)
                data_fine = f"{last_day.strftime('%Y-%m-%d')} 23:59:59"
        except:
            # Fallback al mese corrente
            data_inizio = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            data_fine = datetime.now().strftime('%Y-%m-%d 23:59:59')
    else:  # anno
        data_inizio = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        data_fine = datetime.now().strftime('%Y-%m-%d 23:59:59')
    
    report = db.execute('''
        SELECT 
            d.id, d.nome, d.cognome,
            SUM(CASE WHEN t.fine IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (t.fine - t.inizio)) / 3600 
                ELSE 0 END) as ore_totali
        FROM dipendenti d
        LEFT JOIN timbrature t ON d.id = t.dipendente_id
        WHERE t.inizio >= %s AND t.inizio <= %s
        GROUP BY d.id
        ORDER BY ore_totali DESC
    ''', (data_inizio, data_fine)).fetchall()
    
    result = []
    for row in report:
        result.append({
            'id': row['id'],
            'nome': row['nome'],
            'cognome': row['cognome'],
            'ore_totali': round(row['ore_totali'], 2)
        })
    
    return jsonify(result)

@app.route('/api/report/dipendente/<int:id>')
@login_required
@admin_required
def api_report_dipendente(id):
    db = get_db()
    periodo = request.args.get('periodo', 'mese')
    
    # Ottieni l'anno selezionato (default: anno corrente)
    selected_year = request.args.get('anno', str(datetime.now().year))
    selected_month = request.args.get('mese', str(datetime.now().month))
    current_year = datetime.now().year
    
    # Determina le date di inizio/fine in base al periodo e all'anno
    if periodo == 'mese_specifico':
        try:
            m = int(selected_month)
            y = int(selected_year)
            data_inizio = f"{y}-{m:02d}-01"
            if m == 12:
                data_fine = f"{y}-12-31 23:59:59"
            else:
                next_month = datetime(y, m + 1, 1)
                last_day = next_month - timedelta(days=1)
                data_fine = f"{last_day.strftime('%Y-%m-%d')} 23:59:59"
        except:
             data_inizio = f"{selected_year}-01-01"
             data_fine = f"{selected_year}-12-31 23:59:59"
    elif int(selected_year) == current_year:
        # Logica per l'anno corrente
        if periodo == 'settimana':
            data_inizio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            data_fine = datetime.now().strftime('%Y-%m-%d 23:59:59')
        elif periodo == 'mese':
            data_inizio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            data_fine = datetime.now().strftime('%Y-%m-%d 23:59:59')
        else:  # anno
            data_inizio = f"{selected_year}-01-01"
            data_fine = datetime.now().strftime('%Y-%m-%d 23:59:59')
    else:
        # Logica per anni passati
        if periodo == 'settimana':
            # Ultima settimana dell'anno
            data_inizio = f"{selected_year}-12-24"
            data_fine = f"{selected_year}-12-31 23:59:59"
        elif periodo == 'mese':
            # Ultimo mese dell'anno
            data_inizio = f"{selected_year}-12-01"
            data_fine = f"{selected_year}-12-31 23:59:59"
        else:  # anno
            data_inizio = f"{selected_year}-01-01"
            data_fine = f"{selected_year}-12-31 23:59:59"
            
    timbrature = db.execute('''
        SELECT 
            t.id,
            t.inizio, 
            t.fine,
            CASE WHEN t.fine IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (t.fine - t.inizio)) / 3600 
                ELSE NULL END as ore
        FROM timbrature t
        WHERE t.dipendente_id = %s AND t.inizio >= %s AND t.inizio <= %s
        ORDER BY t.inizio DESC
    ''', (id, data_inizio, data_fine)).fetchall()
    
    dipendente = db.execute('SELECT nome, cognome FROM dipendenti WHERE id = %s', (id,)).fetchone()
    
    result = {
        'nome': dipendente['nome'],
        'cognome': dipendente['cognome'],
        'timbrature': [],
        'anno': selected_year
    }
    
    for t in timbrature:
        inizio = to_datetime(t['inizio'])
        fine = to_datetime(t['fine'])
        
        result['timbrature'].append({
            'id': t['id'],  # Aggiunto ID per la modifica
            'data': inizio.strftime('%d/%m/%Y'),
            'inizio': inizio.strftime('%H:%M:%S'),
            'fine': fine.strftime('%H:%M:%S') if fine else None,
            'ore': round(t['ore'], 2) if t['ore'] is not None else None
        })
    
    return jsonify(result)

@app.route('/api/timbratura/<int:id>', methods=['PUT'])
@login_required
@admin_required
def api_update_timbratura(id):
    data = request.json
    db = get_db()
    
    nuova_data_inizio = data.get('data')  # Formato YYYY-MM-DD (Data Inizio)
    nuovo_inizio = data.get('inizio')  # Formato HH:MM
    
    # Data Fine opzionale (se non c'è, usa Data Inizio)
    nuova_data_fine = data.get('data_fine', nuova_data_inizio)
    nuova_fine = data.get('fine')  # Formato HH:MM (opzionale)
    
    if not all([nuova_data_inizio, nuovo_inizio]):
        return jsonify({'success': False, 'error': 'Dati mancanti'}), 400
        
    try:
        # Costruisci i timestamp completi
        ts_inizio = f"{nuova_data_inizio} {nuovo_inizio}:00"
        ts_fine = f"{nuova_data_fine} {nuova_fine}:00" if nuova_fine else None
        
        # Verifica validità temporale
        if ts_fine:
            dt_inizio = datetime.strptime(ts_inizio, '%Y-%m-%d %H:%M:%S')
            dt_fine = datetime.strptime(ts_fine, '%Y-%m-%d %H:%M:%S')
            if dt_fine <= dt_inizio:
                return jsonify({'success': False, 'error': 'L\'ora di fine deve essere successiva all\'inizio'}), 400
        
        db.execute(
            'UPDATE timbrature SET inizio = %s, fine = %s WHERE id = %s',
            (ts_inizio, ts_fine, id)
        )
        db.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/timbratura/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_timbratura(id):
    db = get_db()
    try:
        db.execute('DELETE FROM timbrature WHERE id = %s', (id,))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/report/mensile')
@login_required
@admin_required
def api_report_mensile():
    db = get_db()
    dipendente_id = request.args.get('dipendente', 'tutti')
    periodo = request.args.get('periodo', 'anno')
    
    # Ottieni l'anno selezionato (default: anno corrente)
    selected_year = request.args.get('anno', str(datetime.now().year))
    selected_month = request.args.get('mese', str(datetime.now().month))
    
    # Default: Anno (Mensile)
    if periodo == 'anno':
        start_date = f"{selected_year}-01-01"
        end_date = f"{selected_year}-12-31 23:59:59"
        
        # Query per raggruppamento mensile
        group_by = "to_char(t.inizio, 'MM')"
        labels = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                  "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        
        # Esegui query
        if dipendente_id != 'tutti':
            report = db.execute(f'''
                SELECT 
                    {group_by} as label_key,
                    SUM(CASE WHEN t.fine IS NOT NULL 
                        THEN EXTRACT(EPOCH FROM (t.fine - t.inizio)) / 3600 
                        ELSE 0 END) as ore_totali
                FROM timbrature t
                WHERE t.dipendente_id = %s AND t.inizio >= %s AND t.inizio <= %s
                GROUP BY label_key
                ORDER BY label_key
            ''', (dipendente_id, start_date, end_date)).fetchall()
        else:
            report = db.execute(f'''
                SELECT 
                    {group_by} as label_key,
                    SUM(CASE WHEN t.fine IS NOT NULL 
                        THEN EXTRACT(EPOCH FROM (t.fine - t.inizio)) / 3600 
                        ELSE 0 END) as ore_totali
                FROM timbrature t
                WHERE t.inizio >= %s AND t.inizio <= %s
                GROUP BY label_key
                ORDER BY label_key
            ''', (start_date, end_date)).fetchall()
            
        # Formatta dati
        data = [0] * 12
        for row in report:
            idx = int(row['label_key']) - 1
            if 0 <= idx < 12:
                data[idx] = round(row['ore_totali'], 2)
                
        return jsonify({
            'labels': labels,
            'data': data,
            'anno': selected_year
        })
        
    else:
        # Periodo: Mese, Mese Specifico, Settimana (Giornaliero)
        if periodo == 'settimana':
            start_date = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d') # Last 7 days including today
            end_date = datetime.now().strftime('%Y-%m-%d 23:59:59')
        elif periodo == 'mese':
            start_date = (datetime.now() - timedelta(days=29)).strftime('%Y-%m-%d') # Last 30 days
            end_date = datetime.now().strftime('%Y-%m-%d 23:59:59')
        elif periodo == 'mese_specifico':
            try:
                m = int(selected_month)
                y = int(selected_year)
                start_date = f"{y}-{m:02d}-01"
                if m == 12:
                    end_date = f"{y}-12-31 23:59:59"
                else:
                    next_month = datetime(y, m + 1, 1)
                    last_day = next_month - timedelta(days=1)
                    end_date = f"{last_day.strftime('%Y-%m-%d')} 23:59:59"
            except:
                start_date = f"{selected_year}-01-01"
                end_date = f"{selected_year}-12-31 23:59:59"
        
        # Query per raggruppamento giornaliero
        # Usa la data completa come chiave per ordinamento e visualizzazione
        group_by = "to_char(t.inizio, 'YYYY-MM-DD')"
        
        params = []
        query_base = f'''
            SELECT 
                {group_by} as data_giorno,
                SUM(CASE WHEN t.fine IS NOT NULL 
                    THEN EXTRACT(EPOCH FROM (t.fine - t.inizio)) / 3600 
                    ELSE 0 END) as ore_totali
            FROM timbrature t
            WHERE t.inizio >= %s AND t.inizio <= %s
        '''
        params.append(start_date)
        params.append(end_date)
        
        if dipendente_id != 'tutti':
            query_base += " AND t.dipendente_id = %s"
            params.append(dipendente_id)
            
        query_base += f" GROUP BY data_giorno ORDER BY data_giorno"
        
        report = db.execute(query_base, params).fetchall()
        
        # Genera labels e data
        # Per semplicità, restituiamo solo i giorni che hanno dati o tutti i giorni nel range%s
        # Meglio tutti i giorni nel range per continuità
        
        labels = []
        data = []
        
        # Mappa dei risultati
        results_map = {row['data_giorno']: row['ore_totali'] for row in report}
        
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date.split(' ')[0], '%Y-%m-%d')
        
        while current <= end:
            day_str = current.strftime('%Y-%m-%d')
            # Format label: dd/mm
            label = current.strftime('%d/%m')
            labels.append(label)
            
            val = results_map.get(day_str, 0)
            data.append(round(val, 2))
            
            current += timedelta(days=1)
            
        return jsonify({
            'labels': labels,
            'data': data,
            'anno': selected_year
        })

@app.route('/api/report/distribuzione')
@login_required
@admin_required
def api_report_distribuzione():
    db = get_db()
    periodo = request.args.get('periodo', 'mese')
    dipendente_id = request.args.get('dipendente', 'tutti')
    selected_year = request.args.get('anno', str(datetime.now().year))
    selected_month = request.args.get('mese', str(datetime.now().month))
    
    # Determina la data di inizio e fine
    data_fine = datetime.now().strftime('%Y-%m-%d 23:59:59')
    
    if periodo == 'settimana':
        data_inizio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    elif periodo == 'mese':
        data_inizio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    elif periodo == 'mese_specifico':
        try:
            m = int(selected_month)
            y = int(selected_year)
            data_inizio = f"{y}-{m:02d}-01"
            if m == 12:
                data_fine = f"{y}-12-31 23:59:59"
            else:
                next_month = datetime(y, m + 1, 1)
                last_day = next_month - timedelta(days=1)
                data_fine = f"{last_day.strftime('%Y-%m-%d')} 23:59:59"
        except:
             data_inizio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    else:  # anno
        data_inizio = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # Costruisci la query SQL
    params = []
    if dipendente_id != 'tutti':
        where_clause = "WHERE t.dipendente_id = %s AND t.inizio >= %s AND t.inizio <= %s AND t.fine IS NOT NULL"
        params = [dipendente_id, data_inizio, data_fine]
    else:
        where_clause = "WHERE t.inizio >= %s AND t.inizio <= %s AND t.fine IS NOT NULL"
        params = [data_inizio, data_fine]
    
    # Query per ottenere la distribuzione oraria per giorno della settimana
    report = db.execute(f'''
        SELECT 
            EXTRACT(DOW FROM t.inizio) as giorno_settimana,
            AVG(CASE WHEN t.fine IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (t.fine - t.inizio)) / 3600 
                ELSE 0 END) as ore_medie
        FROM timbrature t
        {where_clause}
        GROUP BY giorno_settimana
        ORDER BY giorno_settimana
    ''', params).fetchall()
    
    # Prepara i dati per tutti i giorni della settimana (0=domenica, 1=lunedì, ...)
    giorni = ["Domenica", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato"]
    ore_per_giorno = [0] * 7  # Inizializza con 0 ore per ogni giorno
    
    # Popola i dati dai risultati della query
    for row in report:
        idx = int(row['giorno_settimana'])  # Converte da 0-6 a indice
        if 0 <= idx < 7:  # Controllo di sicurezza
            ore_per_giorno[idx] = round(row['ore_medie'], 2)
    
    result = {
        'labels': giorni,
        'data': ore_per_giorno
    }
    
    return jsonify(result)

@app.route('/api/report/confronto')
@login_required
@admin_required
def api_report_confronto():
    db = get_db()
    periodo = request.args.get('periodo', 'mese')
    
    # Ottieni l'anno selezionato (default: anno corrente)
    selected_year = request.args.get('anno', str(datetime.now().year))
    selected_month = request.args.get('mese', str(datetime.now().month))
    
    # Determina la data di inizio in base al periodo
    if periodo == 'mese':
        # Ultimo mese: prendere da 30 giorni fa fino ad oggi se anno corrente,
        # altrimenti prendere l'ultimo mese dell'anno selezionato
        current_year = datetime.now().year
        if int(selected_year) == current_year:
            data_inizio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            data_fine = datetime.now().strftime('%Y-%m-%d')
        else:
            data_inizio = f"{selected_year}-12-01"
            data_fine = f"{selected_year}-12-31"
    elif periodo == 'mese_specifico':
        try:
            m = int(selected_month)
            y = int(selected_year)
            data_inizio = f"{y}-{m:02d}-01"
            if m == 12:
                data_fine = f"{y}-12-31"
            else:
                next_month = datetime(y, m + 1, 1)
                last_day = next_month - timedelta(days=1)
                data_fine = last_day.strftime('%Y-%m-%d')
        except:
             data_inizio = f"{selected_year}-01-01"
             data_fine = f"{selected_year}-12-31"
    else:  # anno
        data_inizio = f"{selected_year}-01-01"
        data_fine = f"{selected_year}-12-31"
    
    # Ottieni tutti i dipendenti attivi
    dipendenti = db.execute('''
        SELECT id, nome, cognome 
        FROM dipendenti 
        ORDER BY cognome, nome
    ''').fetchall()
    
    result = {
        'labels': [],
        'datasets': [],
        'anno': selected_year
    }
    
    if periodo == 'mese' or periodo == 'mese_specifico':
        # Query per ottenere ore per dipendente nel periodo selezionato (una singola barra per dipendente)
        result['labels'] = ["Ore Lavorate"]
        
        # Definiamo alcuni colori per i diversi dipendenti
        colori = [
            'rgba(54, 162, 235, 0.7)', 'rgba(255, 99, 132, 0.7)', 'rgba(75, 192, 192, 0.7)', 
            'rgba(255, 206, 86, 0.7)', 'rgba(153, 102, 255, 0.7)', 'rgba(255, 159, 64, 0.7)',
            'rgba(199, 199, 199, 0.7)', 'rgba(83, 102, 255, 0.7)', 'rgba(40, 167, 69, 0.7)'
        ]
        
        for idx, dip in enumerate(dipendenti):
            color_idx = idx % len(colori)
            
            ore_totali = db.execute('''
                SELECT 
                    SUM(CASE WHEN t.fine IS NOT NULL 
                        THEN EXTRACT(EPOCH FROM (t.fine - t.inizio)) / 3600 
                        ELSE 0 END) as ore_totali
                FROM timbrature t
                WHERE t.dipendente_id = %s AND t.inizio >= %s AND t.inizio <= %s
            ''', (dip['id'], data_inizio, data_fine)).fetchone()['ore_totali'] or 0
            
            result['datasets'].append({
                'label': f"{dip['cognome']} {dip['nome']}",
                'data': [round(ore_totali, 2)],
                'backgroundColor': colori[color_idx],
                'borderColor': colori[color_idx].replace('0.7)', '1)'),
                'borderWidth': 1
            })
    else:  # anno - mostra l'andamento mensile per ciascun dipendente
        # Prepara le etichette dei mesi
        mesi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
        result['labels'] = mesi
        
        # Definiamo alcuni colori per i diversi dipendenti
        colori = [
            'rgba(54, 162, 235, 1)', 'rgba(255, 99, 132, 1)', 'rgba(75, 192, 192, 1)', 
            'rgba(255, 206, 86, 1)', 'rgba(153, 102, 255, 1)', 'rgba(255, 159, 64, 1)',
            'rgba(199, 199, 199, 1)', 'rgba(83, 102, 255, 1)', 'rgba(40, 167, 69, 1)'
        ]
        
        for idx, dip in enumerate(dipendenti):
            color_idx = idx % len(colori)
            
            # Query per ottenere le ore mensili del dipendente
            report = db.execute('''
                SELECT 
                    to_char(t.inizio, 'MM') as mese,
                    SUM(CASE WHEN t.fine IS NOT NULL 
                        THEN EXTRACT(EPOCH FROM (t.fine - t.inizio)) / 3600 
                        ELSE 0 END) as ore_totali
                FROM timbrature t
                WHERE t.dipendente_id = %s AND t.inizio >= %s AND t.inizio <= %s
                GROUP BY 1
                ORDER BY 1
            ''', (dip['id'], data_inizio, data_fine)).fetchall()
            
            # Inizializza un array di 12 elementi con 0 ore
            ore_mensili = [0] * 12
            
            # Popola i dati dai risultati della query
            for row in report:
                mese_idx = int(row['mese']) - 1  # Converte da 01-12 a 0-11 per l'indice
                if 0 <= mese_idx < 12:  # Controllo di sicurezza
                    ore_mensili[mese_idx] = round(row['ore_totali'], 2)
            
            # Aggiungi il dataset per questo dipendente
            result['datasets'].append({
                'label': f"{dip['cognome']} {dip['nome']}",
                'data': ore_mensili,
                'borderColor': colori[color_idx],
                'backgroundColor': colori[color_idx].replace('1)', '0.1)'),
                'fill': False,
                'tension': 0.1
            })
    
    return jsonify(result)

@app.route('/api/stato-dipendenti')
def api_stato_dipendenti():
    db = get_db()
    dipendenti = db.execute('''
        SELECT 
            d.id, d.nome, d.cognome,
            t.inizio,
            t.id as timbratura_id
        FROM dipendenti d
        LEFT JOIN (
            SELECT * FROM timbrature 
            WHERE fine IS NULL 
            ORDER BY inizio DESC
        ) t ON d.id = t.dipendente_id
        ORDER BY d.cognome, d.nome
    ''').fetchall()
    
    result = []
    for d in dipendenti:
        stato = {
            'id': d['id'],
            'nome': d['nome'],
            'cognome': d['cognome'],
            'presente': d['inizio'] is not None,
            'inizio': None
        }
        
        if d['inizio']:
            inizio = to_datetime(d['inizio'])
            stato['inizio'] = inizio.strftime('%d/%m/%Y %H:%M:%S')
        
        result.append(stato)
    
    return jsonify(result)

def create_app():
    return app

if __name__ == '__main__':
    # Inizializzazione del database all'avvio (create tables if not exists)
    with app.app_context():
        # init_db() # Optional: auto-init schema. For now disable to rely on migration/manual init
        pass
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5003)), debug=True)