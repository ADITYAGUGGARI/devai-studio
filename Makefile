PYTHON ?= python3
VENV := .venv/bin

.PHONY: setup setup-api dev-api dev-web dev-mobile scheduler worker test lint format check

setup: setup-api
	npm ci
	npm --prefix web ci
	npm --prefix mobile ci

setup-api:
	$(PYTHON) -m venv .venv
	$(VENV)/python -m pip install -c api/constraints.txt -e './api[dev]'

dev-api:
	$(VENV)/uvicorn devai.main:app --app-dir api/src --reload --reload-dir api/src --reload-exclude .venv --host 127.0.0.1 --port 8000 --env-file .env

dev-web:
	npm run dev:web

dev-mobile:
	npm run dev:mobile

scheduler:
	$(VENV)/python -m devai.scheduler

worker:
	$(VENV)/python -m devai.worker

test:
	PYTHONPATH=api/src $(VENV)/python -m pytest -c api/pyproject.toml api/tests

lint:
	$(VENV)/ruff check api
	$(VENV)/ruff format --check api
	npm run lint
	npm run format:check

format:
	$(VENV)/ruff check --fix api
	$(VENV)/ruff format api
	npm run format

check: lint test
	npm run typecheck
	npm run build

# Integration tests use disposable PostgreSQL schemas.
test-postgres:
	TEST_DATABASE_URL=postgresql+psycopg://devai:devai_local_only@127.0.0.1:$${POSTGRES_PORT:-5433}/devai $(MAKE) test

migrate:
	$(VENV)/python -m devai.migrate upgrade head

test-web-connected:
	npm run test:e2e:connected

bundle-ios:
	cd mobile && npx expo export --platform ios --output-dir ../.local-data/mobile-ios-bundle
