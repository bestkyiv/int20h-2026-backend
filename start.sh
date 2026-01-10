#!/bin/sh
set -e

# Run migrations
echo "Running migrations..."
alembic upgrade head

# Run seeds
echo "Running seeds..."
python scripts/seed.py

# Start the application
echo "Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
