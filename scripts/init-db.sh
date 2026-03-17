#!/bin/bash
set -e

echo "=== Initializing JobPilot Database ==="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until docker compose exec postgres pg_isready -U jobpilot -d jobpilot_db; do
    sleep 2
done
echo "PostgreSQL is ready."

# Run Alembic migrations
echo "Running database migrations..."
docker compose exec backend alembic upgrade head

# Seed initial data
echo "Seeding initial data..."
docker compose exec backend python scripts/seed-data.py

echo "=== Database Initialization Complete ==="
