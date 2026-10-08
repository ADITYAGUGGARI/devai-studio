# Local startup and verification

Use Node 22.13+ and Python 3.13. Keep server/provider secrets in ignored root `.env`. Never put provider credentials in `VITE_` or `EXPO_PUBLIC_` values.

1. Copy `.env.example` only for a new checkout. Preserve an existing `.env`.
2. Set `ADMIN_EMAIL` and a unique `ADMIN_PASSWORD` of at least 12 characters. The first startup creates the admin only when no accounts exist; changing environment values does not reset existing passwords.
3. Run `make setup`, then `docker compose up -d postgres`.
4. Run `make migrate`, `make dev-api`, and `make dev-web` in separate terminals.
5. Open http://localhost:5173. Swagger is http://localhost:8000/docs. Sign in with the configured account. The current development checkout stores its generated admin login in ignored `.local-data/admin-login.txt` (mode 600).
6. Review research evidence, verify manual excerpts, approve a topic, select eight slides, and generate. Background jobs retain progress/retries in PostgreSQL. Review every source and image before approval. Editing or regeneration invalidates approval.
7. Enable daily research and choose hour/timezone in Operations. `DAILY_WEB_SEARCH=true` adds real provider-backed web search to daily research. Without it, dated publisher RSS and source retrieval remain available. Automatic drafting consumes only previously approved topics.
8. Add `OPENAI_API_KEY` on the server for writing, factual checks, web search and images. Missing billing/model access is reported as a real failure. Image generation composes the entire slide; processing only validates/converts/resizes/exports.
9. Add Meta professional-account credentials and a public HTTPS API origin for Instagram. Publishing requires an approved unchanged version and valid media. No automatic recovery resends an uncertain publication: reconcile it against Instagram first.

## Preserve an existing SQLite workspace

Stop API and workers before `PYTHONPATH=api/src .venv/bin/python -m devai.transfer`. See CLI `--help`. Import only into an empty PostgreSQL workspace. The importer makes a SQLite backup and copies all application tables inside one transaction. It refuses active jobs and nonempty targets. Keep artwork directories alongside database backups: the database retains file references, not image bytes.

## Verification

- `make check`: formatting, lint, backend suite, both TypeScript clients and Vite build.
- `make test-postgres`: same API/workflow suite in disposable PostgreSQL schemas, without changing workspace data.
- `npm run test:e2e`: isolated browser tests with explicitly mocked providers/API responses.
- `npm run test:e2e:connected`: actual FastAPI + PostgreSQL + account cookies; queue approval, edit/restore, review guard, axe accessibility and screenshot comparisons. Test fixtures are identified as isolated test content. No provider/publishing calls.
- `make bundle-ios`: native Hermes bundle generation. This is not simulator acceptance.
- For native acceptance: install full Xcode and an iOS runtime; install Maestro. Start `PYTHONPATH=api/src .venv/bin/python scripts/e2e_server.py`, set `EXPO_PUBLIC_API_URL=http://127.0.0.1:8124` for a simulator development build, then run `npx expo run:ios` from `mobile` and `maestro test mobile/.maestro/editorial.yaml` from the root. Use a fresh isolated simulator. Never run these test credentials against production.

Screenshot baselines are platform-specific. Inspect changed images before accepting new baselines. Provider tests incur real usage and must never publish during automated acceptance.
