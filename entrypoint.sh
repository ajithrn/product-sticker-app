#!/bin/sh

# Load environment variables from .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Extract the database name from DATABASE_URL
DB_NAME=$(echo $DATABASE_URL | sed -E 's/.*\/([^/]+)$/\1/')

# Ensure backup directory exists and has correct permissions
mkdir -p /app/backups
chmod 755 /app/backups

# Ensure instance directory exists and has correct permissions
mkdir -p /app/instance
chmod 755 /app/instance

# Create an empty database file if it doesn't exist
touch /app/instance/$DB_NAME
chmod 644 /app/instance/$DB_NAME

# Initialize the database if it hasn't been initialized yet
if [ ! -f /app/instance/database_initialized ]; then
  flask db init
  touch /app/instance/database_initialized
fi

# Apply database migrations
flask db migrate -m "Auto-generated migration" || true
flask db upgrade

# Start the application
if [ "$FLASK_ENV" = "development" ]; then
    echo "Starting Flask development server..."
    flask run --host=0.0.0.0 --port=5000
else
    echo "Starting Gunicorn production server..."
    gunicorn --bind 0.0.0.0:5000 run:app
fi