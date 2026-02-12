# -------- Makefile for InglewoodCrawler --------
ENV_FILE ?= .env.dev
PROFILES ?= dev

_up = docker compose --env-file $(ENV_FILE) --profile $(PROFILES)

# Existing commands (UNCHANGED)
up-dev:
	docker compose --env-file .env.dev --profile dev up -d db api scheduler

up-prod:
	docker compose --env-file .env.prod --profile prod up -d db api scheduler proxy

# Stop everything
.PHONY: down
down:
	docker compose --env-file .env.dev --profile dev down || true
	docker compose --env-file .env.dev --profile prod -f docker-compose.yml -f docker-compose.prod.yml down || true

logs:
	$(_up) logs -f

ps:
	$(_up) ps

rebuild:
	docker compose build --no-cache

shell-db:
	docker exec -it igw_db psql -U postgres -d inglewood

shell-api:
	docker exec -it igw_api bash

check:
	curl http://localhost:8000/healthz

# NEW: Test production build locally
up-prod-local:
	docker compose --env-file .env.dev --profile prod -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# NEW: Manual ingestion
ingest:
	docker exec -it igw_scheduler python -u ingest_pg.py

# NEW: Reset database
reset-db:
	docker exec -it igw_db psql -U postgres -d inglewood -c "TRUNCATE TABLE events;"
	@echo "Database cleared! Run 'make ingest' to repopulate"
