# Development standards

Run commands from the repository root unless a command names another directory. Install dependencies with `make setup`, then run `make check` before submitting changes.

## Python

- Use the `devai` package and absolute imports. Do not modify `sys.path` in application code or tests.
- Keep assembly in `main.py`, configuration/database setup in `core`, persistence in `models`, inputs in `schemas`, and external adapters in `integrations`.
- Keep reusable discovery, generation, rendering, and deduplication in `services`. Routes handle requests and transaction boundaries.
- Use four-space indentation, type annotations on new interfaces, and Ruff's imports and formatting. Use UTC timestamps.
- Imports must not create tables, make provider requests, or start workers. App lifespan and explicit commands own startup.
- Use the `client` fixture for HTTP tests. Mock provider calls; never rely on local credentials, live feeds, or a shared database.
- Preserve stored column names and types until a versioned migration is introduced.

## TypeScript and UI

- Keep entry points small. Group components by feature; put HTTP behavior in `services` and API shapes in `types`.
- Use strict TypeScript, typed request/response interfaces, accessible labels, and appropriate button states.
- Keep credentials and provider calls on the server. Client environment variables are public.
- Use ESLint and Prettier. Commit updated lockfiles with dependency changes; use `npm ci` for clean installs.
- Validate Expo upgrades on a device or simulator, not only with TypeScript.

## Content and publishing

Drafts remain unverified until reviewed. Preserve source attribution. Edits invalidate approval, and publishing reserves a version before calling Meta. Failed or uncertain publication requires reconciliation; do not add blind retries.

Add focused regression tests when changing approval, deduplication, rendering, provider failures, or persistence. Document limits instead of claiming unavailable automation or originality guarantees.

## Dependencies

Python ranges live in `api/requirements.txt` and `api/pyproject.toml`; resolved versions are in `api/constraints.txt`. Refresh constraints in a clean environment, omit editable/local paths, and check supported Python versions. Each JavaScript project has its own manifest and lockfile; the root provides development tooling and orchestration.
