#!/bin/bash
set -e

echo "=== JobPilot Production Deployment ==="

# Load environment
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    exit 1
fi

source .env

echo "1. Pulling latest code..."
git pull origin main

echo "2. Building production images..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

echo "3. Running database migrations..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm backend alembic upgrade head

echo "4. Deploying services..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo "5. Waiting for services to start..."
sleep 10

echo "6. Running health checks..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend python scripts/healthcheck.py || true

echo "7. Cleaning up old images..."
docker image prune -f

echo ""
echo "=== Deployment Complete ==="
echo "Frontend: https://${DOMAIN}"
echo "API: https://api.${DOMAIN}"
echo "RabbitMQ: http://localhost:15672"
