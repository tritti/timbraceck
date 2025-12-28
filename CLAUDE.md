# CLAUDE.md - Development Guidelines

## Commands
- Setup: `python -m venv venv && source venv/bin/activate`
- Install: `pip install -r requirements.txt`
- Initialize DB: `python init_db.py`
- Populate test data: `python populate_db.py`
- Run app: `python app.py`

## Code Style
- Python: 4 spaces indentation, snake_case for functions/variables
- SQL: Uppercase keywords, parameterized queries for security
- Routes: Group by functionality (main, admin, API)
- Error handling: Use try/except with specific exceptions
- Security: Password hashing, session authentication, parameterized queries
- JSS: camelCase for functions, event-driven approach

## Structure
- MVC-like: Routes in app.py, templates in templates/, database in database/
- Authentication: Flask session-based, decorator for protected routes
- Database: SQLite with sqlite3 connector
- Date handling: Use datetime objects consistently 
- API endpoints: Return JSON responses with jsonify