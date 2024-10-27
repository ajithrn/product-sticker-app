#!/bin/sh

# Set default value if not provided
: "${FLASK_ENV:=production}"

# Ensure backup directory exists and has correct permissions
mkdir -p /app/backups
chmod 755 /app/backups

# Ensure instance directory exists and has correct permissions
mkdir -p /app/instance
chmod 755 /app/instance

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Initialize database with migrations
echo "Running database migrations..."
export FLASK_APP=run.py
export DATABASE_URL=postgresql://postgres:postgres@db:5432/product_sticker_app
export DOCKER_ENV=true

# Run migrations
flask db upgrade

# Start the application based on environment
if [ "$FLASK_ENV" = "development" ]; then
    echo "Starting Flask development server with hot reload..."
    # Use Flask development server with hot reload
    flask run --host=0.0.0.0 --port=5000 --reload
else
    echo "Starting Gunicorn production server..."
    gunicorn --bind 0.0.0.0:5000 run:app
fi
