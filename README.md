# DevAI Studio

Research AI developments for software engineers, turn verified sources into original Instagram carousels, and review every post before publication.

The project contains a FastAPI API, a React dashboard, and an Expo mobile review app. It supports source discovery, draft generation from a supplied excerpt, editing, approval, and 1080 × 1350 PNG export. The full daily research-to-finished-carousel workflow is still under development.

## Repository layout

```text
api/
  src/devai/
    core/           Configuration, authentication, database setup
    models/         SQLAlchemy persistence models
    schemas/        Validated API inputs
    routes/         Posts, research, exports, publishing
    services/       Discovery, drafting, URL deduplication, rendering
    integrations/   Instagram API adapter
    main.py         Application factory and router registration
    scheduler.py    Single-instance discovery worker
  tests/            Isolated API and service tests
web/src/
  app/              Application shell and providers
  features/         Post library/editor and research form
  services/         HTTP client and downloads
  types/            TypeScript API contracts
  data/             Editable starter content
mobile/src/
  app/              Review application
  services/         Mobile HTTP client
  types/            Mobile API contracts
docs/               Architecture, product scope, development roadmap
```

## Run locally

Use Python 3.13 and Node 22 (`nvm use` if you use nvm). Python 3.12+ is supported by the package. Native development uses SQLite and does not require Docker, an AI key, or Instagram credentials.

From the repository root:

```bash
cp .env.example .env
cp web/.env.example web/.env
cp mobile/.env.example mobile/.env
make setup
```

Run each service in its own terminal:

```bash
make dev-api
make dev-web
```

Open the dashboard at <http://localhost:5173> and API documentation at <http://localhost:8000/docs>. Create a starter draft, edit its slides, submit it for review, approve it, and export its PNG ZIP. Add `OPENAI_API_KEY` to the root `.env` to enable generation from a source excerpt. Restart the API after changing its environment. The model and Graph API defaults are inherited configuration, not assertions about current provider availability.

`ADMIN_API_KEY` and `web/.env`'s `VITE_ADMIN_API_KEY` must match. The default key is for local development only. Vite environment values are visible to browser users; do not put provider secrets in a `VITE_` variable. Real account authentication is a prerequisite for public deployment.

For mobile, run `make dev-mobile`. A physical device needs `EXPO_PUBLIC_API_URL` set to your computer's LAN address and the API listening on that interface; the native API command binds only to loopback by default. Enter the development API key in the app. Native iOS/Android packaging is not part of the current checks.

## Docker development

```bash
docker compose up --build
```

The same web/API URLs apply. PostgreSQL is available on loopback port 5433 by default to avoid competing with other local projects. Compose waits for database/API health before starting dependent services. This is a development setup, including the Vite dev server and local database password.

## Daily discovery

Start exactly one scheduler against a database:

```bash
make scheduler
# Or with Docker:
docker compose --profile automation up --build
```

The worker checks once a minute and creates up to five unverified editorial scaffolds at or after 8 AM `America/Chicago`. Configure `DAILY_TIMEZONE` and `DAILY_HOUR` in `.env`. It must remain running; this setup does not install an OS background service or modify a ChatGPT scheduled task. It does not generate final AI copy, export images, approve, or publish automatically. Its last-run date is in memory; canonical URL deduplication persists, but durable scheduling and concurrent ingestion are still planned. Do not manually ingest while the worker is running.

## Quality checks

```bash
make check          # Tests, lint/format checks, client type checks, web build
make test           # API and service tests only
make format         # Apply Ruff and Prettier formatting
```

CI runs equivalent checks on pushes and pull requests. Each HTTP test gets its own in-memory database. Tests use fake provider responses and do not publish to Instagram or spend AI credits. npm lockfiles and `api/constraints.txt` capture resolved dependencies; update them deliberately.

## Current limits and next work

- Originality checks cover canonical source URLs in daily discovery and title similarity during AI generation. They do not compare against all Instagram creators or guarantee unique content.
- Source verification, topic rotation, original examples, and automatic final carousel production are the next content-pipeline milestone.
- The Instagram adapter is exercised with fakes. Live publishing still needs verified credentials, public JPEG media hosting, media-to-approved-version validation, and production concurrency checks. Export currently produces PNGs.
- Tables are created during startup for development. Versioned migrations and production authentication remain planned.
- The inherited Expo 54 dependency tree has npm audit findings; upgrade it separately with device validation before distribution.

See [product requirements](docs/product.md), [architecture](docs/architecture.md), [roadmap](docs/roadmap.md), and [contribution standards](CONTRIBUTING.md).
