.PHONY: dev up down build logs migrate seed clean

# Development
dev:
	docker compose up --build

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

# Database
migrate:
	docker compose exec backend alembic upgrade head

migrate-create:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

seed:
	docker compose exec backend python scripts/seed-data.py

# Individual services
backend-shell:
	docker compose exec backend bash

frontend-shell:
	docker compose exec frontend sh

db-shell:
	docker compose exec postgres psql -U jobpilot -d jobpilot_db

redis-shell:
	docker compose exec redis redis-cli

# Cleanup
clean:
	docker compose down -v --remove-orphans
	docker system prune -f

# Production
prod-up:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-build:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Testing
test-backend:
	docker compose exec backend pytest tests/ -v

test-frontend:
	docker compose exec frontend npm test
