PYTHON ?= python3
VENV := .venv/bin

.PHONY: setup setup-api dev-api dev-web dev-mobile scheduler test lint format check

setup: setup-api
	npm ci
	npm --prefix web ci
	npm --prefix mobile ci

setup-api:
	$(PYTHON) -m venv .venv
	$(VENV)/python -m pip install -c api/constraints.txt -e './api[dev]'

dev-api:
	$(VENV)/uvicorn devai.main:app --reload --host 127.0.0.1 --port 8000 --env-file .env

dev-web:
	npm run dev:web

dev-mobile:
	npm run dev:mobile

scheduler:
	$(VENV)/devai-scheduler

test:
	$(VENV)/python -m pytest -c api/pyproject.toml api/tests

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
