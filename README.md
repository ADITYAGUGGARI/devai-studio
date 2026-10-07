# DevAI Studio

Research AI developments for software engineers, turn verified sources into original Instagram carousels, and review every post before publication.

The project contains a FastAPI API, a React dashboard, and an Expo mobile review app. It supports daily primary-source discovery, source-grounded eight-slide draft generation, editing, approval, and 1080 × 1350 PNG export. Every generated post remains a draft until a person reviews and approves it.

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

Open the dashboard at <http://localhost:5173> and API documentation at <http://localhost:8000/docs>. Create a starter draft, edit its slides, submit it for review, approve it, and export its PNG ZIP. Add `OPENAI_API_KEY` to the root `.env` to enable text generation. In a draft editor, **Create unique AI artwork for all slides** requests one original image per slide; exact copy is typeset over each image. This makes eight image-generation API calls and may incur charges. Restart the API after changing its environment. The model and Graph API defaults are inherited configuration, not assertions about current provider availability.

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

The worker checks once a minute and prepares one source-grounded eight-slide draft on or after `DAILY_HOUR` (8 AM by default) in `DAILY_TIMEZONE` (`America/Chicago` by default). It reads official feeds from GitHub, Google Developers, OpenAI, the Claude Code changelog, the Codex and MCP repositories, and arXiv. It records a source excerpt and retrieval date, follows the rotating editorial mix, and saves the caption, hashtags, evidence, and run history. The Dashboard can also start the day's run with **Prepare today's carousel**. Once complete, **Research another story** creates a separate draft from a recent source not already used, leaving today's run intact. Both drafts remain unapproved; review the copy and source before exporting 1080 × 1350 images from the editor.

Set `OPENAI_API_KEY` in the server-side root `.env` to create carousel copy. For example, replace the empty `OPENAI_API_KEY=` line in `.env` with the key from your OpenAI API account. Keep this key out of client `.env` files and source control. Restart `make dev-api` and `make scheduler` after changing it. If a run previously failed only because the key was missing, the Dashboard enables an immediate retry after the API has loaded the key. If no recent source qualifies, all feeds fail, or generation is unavailable, the run creates no fabricated post. Other transient failures are retried up to three times at 30-minute intervals. Keep exactly one scheduler running and do not also run another scheduler replica. This command runs in the foreground; it does not install an OS service or change a ChatGPT scheduled task. `POST /research/ingest` remains available in Swagger as a separate, explicitly unverified link-scaffold import.

## Quality checks

```bash
make check          # Tests, lint/format checks, client type checks, web build
make test           # API and service tests only
make format         # Apply Ruff and Prettier formatting
```

CI runs equivalent checks on pushes and pull requests. Each HTTP test gets its own in-memory database. Tests use fake provider responses and do not publish to Instagram or spend AI credits. npm lockfiles and `api/constraints.txt` capture resolved dependencies; update them deliberately.

## Built and remaining

See [feature status](docs/features.md) for the implemented product areas, operational setup, and remaining work. The reusable editorial and originality guidance lives in [the project skill](.agents/skills/devai-instagram-editorial/SKILL.md).

## Current limits and next work

- Originality checks cover canonical source URLs in daily discovery and title similarity during AI generation. They do not compare against all Instagram creators or guarantee unique content.
- Generated drafts use source excerpts, attribution, a developer-focused editorial angle, and an enforced topic rotation. A human must fact-check claims, review the code/examples, and export the images before posting.
- The Instagram adapter is exercised with fakes. Live publishing still needs verified credentials, public JPEG media hosting, media-to-approved-version validation, and production concurrency checks. Export currently produces PNGs.
- Tables are created during startup for development. Versioned migrations and production authentication remain planned.
- The inherited Expo 54 dependency tree has npm audit findings; upgrade it separately with device validation before distribution.

See [product requirements](docs/product.md), [architecture](docs/architecture.md), [roadmap](docs/roadmap.md), and [contribution standards](CONTRIBUTING.md).
