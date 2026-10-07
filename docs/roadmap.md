# Development roadmap

## Foundation — implemented locally

- Backend package with separate configuration, models, schemas, routes, services, and adapters.
- Application factory, isolated database fixtures, no schema creation during import.
- Feature-oriented dashboard, typed HTTP clients, mobile source organization.
- Portable PNG export, corrected publish route registration, failure-path regression coverage.
- EditorConfig, Ruff, ESLint, Prettier, TypeScript checks, dependency snapshots, CI, environment examples, Docker health checks.

## Daily pipeline — first pass implemented

- Official feeds for GitHub, Google Developers, OpenAI, Anthropic Claude Code, OpenAI Codex, MCP, and two arXiv categories. Only source-dated stories from the last 14 days enter selection.
- Bounded HTTPS source fetching with publisher-host allowlists and redirects disabled.
- One durable run per local day, up to three attempts, duplicate source/title avoidance, and a 20-day weighted topic calendar.
- Grounded eight-slide text, caption, hashtags, source excerpt, publication/retrieval dates, and an editorial angle are saved on the draft.
- Dashboard view and manual trigger share the scheduler's daily lock. All generated posts remain unapproved.

## Next: make the pipeline production-ready

1. Introduce versioned database migrations; daily runs and source metadata are already persisted in the current schema.
2. Expand publisher coverage, expose feed-level diagnostics, and validate candidate ranking with real days of results.
3. Store topic/angle history across all draft entry points and add stronger similarity checks against slide copy.
4. Add visual diagrams or image layouts driven by verified technical concepts; currently the generated carousel is typography on the shared slide design.
5. Validate the weighted schedule and source matching against an editorial review set.
6. Add dashboard controls for source comparison and originality findings.

See [feature status](features.md) for the full implementation inventory, prerequisites, and remaining validation.

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
