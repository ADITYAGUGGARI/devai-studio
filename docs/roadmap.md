# Development roadmap

## Foundation — implemented locally

- Backend package with separate configuration, models, schemas, routes, services, and adapters.
- Application factory, isolated database fixtures, no schema creation during import.
- Feature-oriented dashboard, typed HTTP clients, mobile source organization.
- Portable PNG export, corrected publish route registration, failure-path regression coverage.
- EditorConfig, Ruff, ESLint, Prettier, TypeScript checks, dependency snapshots, CI, environment examples, Docker health checks.

## Next: complete the daily content pipeline

1. Introduce migrations, durable runs, and source metadata including publication/retrieval times.
2. Expand primary sources and rank fresh stories; implement the agreed topic mix.
3. Store topics, angles, examples, and source identities across all draft entry points; add meaningful similarity checks.
4. Build source-backed drafts with original examples, verification flags, captions, hashtags, and rendered images.
5. Produce one package per daily run; make retries idempotent and report failures without invented content.
6. Add dashboard views for source evidence, run status, and originality findings.

## Before public deployment or live publishing

- Replace development keys with account authentication and authorization.
- Bind hosted JPEG media to approved versions and verify Meta behavior with a designated test account.
- Test concurrent editing, approval, ingestion, and publishing on PostgreSQL; implement durable scheduling locks.
- Add deployment secrets, backups, observability, and reconciliation tools.
- Validate browser behavior and native mobile packaging on devices/simulators.
- Resolve inherited Expo 54 dependency advisories through a tested upgrade. Initial install reported 35 findings (12 moderate, 23 high); counts change with advisory updates.

## Validation notes

The original checkout had 21 passing backend tests and one Linux-font-path export failure. The web build failed because Vite environment types were absent. Regression coverage now includes these fixes and the formerly shadowed publish route with fake adapters.

Native development is the verification target for this reorganization. Docker and CI configuration are supplied; container builds, hosted CI, native mobile packaging, live feeds, paid generation, and live Instagram publication require separate verification.

Local foundation validation completed with Python 3.13.15 and Node 22.23.3: 31 backend tests passed; Ruff, ESLint, Prettier, both TypeScript checks, the web build, and Docker Compose configuration validation passed. The API health endpoint and dashboard entry page responded successfully. A rendered sample PNG was visually inspected. A browser interaction walkthrough was unavailable because Computer Use permissions were not granted.
