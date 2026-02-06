# -------- Makefile for InglewoodCrawler --------
ENV_FILE ?= .env.dev
PROFILES ?= dev

_up = docker compose --env-file $(ENV_FILE) --profile $(PROFILES)

up-dev:
	docker compose --env-file .env.dev --profile dev up -d db api scheduler

up-prod:
	docker compose --env-file .env.prod --profile prod up -d db api scheduler proxy

down:
	$(_up) down

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
