#!/bin/bash
set -e

# Database path from environment or default
DB_PATH=${DATABASE_PATH:-/app/data/timbrature.db}
DB_DIR=$(dirname "$DB_PATH")

# Ensure data directory exists and has correct permissions
mkdir -p "$DB_DIR"
chown -R appuser:appuser "$DB_DIR"

# Initialize database if it doesn't exist
if [ ! -f "$DB_PATH" ]; then
    echo "Database not found at $DB_PATH. Initializing..."
    
    # Update app.py to use the correct database path
    export DATABASE=$DB_PATH
    
    # Run database initialization as appuser
    gosu appuser python init_db.py
    
    echo "Database initialized successfully!"
else
    echo "Database found at $DB_PATH. Skipping initialization."
fi

# Start the application with Gunicorn as appuser
echo "Starting application with Gunicorn..."
exec gosu appuser gunicorn --bind 0.0.0.0:5003 \
    --workers 2 \
    --threads 4 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    "app:create_app()"
