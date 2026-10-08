# Production readiness assessment

This branch prepares deployment; no production deployment or live Instagram publication has been performed.

## Implemented controls

- Persistent PostgreSQL state, static Alembic migrations, database readiness, durable jobs with conditional claims/leases, resumable image work and conservative publication reconciliation.
- Scrypt password hashes, opaque persisted hashed sessions, expiry/logout, account roles, persistent login throttling, credential-free client bundles, cookie origin checks and authenticated private images.
- Production configuration rejects SQLite, development API keys, insecure cookies and HTTP CORS origins. Run migrations explicitly before API, worker or scheduler startup; production defaults to `AUTO_MIGRATE=false`.
- Request IDs/status/latency logs, job diagnostics/progress and worker heartbeat in `/ops/summary`. Provider usage records tokens/images, durations/failures and optional configured cost estimates. Estimates without rates remain unknown.
- Version-bound topic/content approval, immutable artwork versions and media snapshots, scheduling checks and no automatic retries of uncertain publishing outcomes.
- Actual local backup/restore verification in a disposable PostgreSQL database. Archive the database and immutable artwork/media together. Do not automatically delete historical images referenced by revisions.

## Deployment procedure

Provision PostgreSQL, persistent shared artwork/media volumes, TLS ingress and server-only secrets. Set `APP_ENV=production`, `ALLOW_DEV_API_KEY=false`, `COOKIE_SECURE=true`, `AUTO_MIGRATE=false`, HTTPS `CORS_ORIGINS`, and a public HTTPS media origin. Use a same-site web/API deployment for strict session cookies. Route reverse-proxy origins correctly; configure trusted proxy handling and rate limiting at ingress. Run `python -m devai.migrate upgrade head` as a single deployment step before starting replicas. Turn off the embedded worker when operating standalone workers. All workers must share the same database and immutable asset storage.

Build the web bundle with its public API origin. Build/sign iOS with its public HTTPS API origin and a reviewed development/production Expo configuration. Store native bearer sessions in SecureStore; avoid logs containing authorization headers. Use secret rotation and encrypted backups managed by the chosen deployment platform. Test restore into a new database before cutover; never downgrade/drop a populated production schema without a tested backup.

Monitor `/ready`, authenticated `/ops/summary`, stale job leases, failed jobs, missing worker heartbeat, source diagnostics, provider quota and Meta permissions. The worker heartbeat indicates recent process activity, not provider health. Keep public signed media for the needed Meta retrieval/reconciliation window; retention requires reconciliation-aware operational policy.

## Acceptance blockers and limits

- Xcode 27/iOS 27 and Device Hub are installed. Expo Go runs locally and a native review screenshot was inspected. Standalone native packaging requires CocoaPods; the prepared Maestro flow has not yet been executed. Hermes export and a screenshot do not establish complete native acceptance.
- Meta token, professional account and public HTTPS origin are absent. Official integration and uncertain-outcome controls are tested with isolated adapters, but permissions, public image fetching, container processing and actual publication require a designated test account.
- Native dependency audit still reports 35 inherited issues (12 moderate, 23 high). Compatible `npm audit fix` did not resolve them; suggested fixes require incompatible Expo/React Native changes. Do not use forced major changes before a supported SDK migration and simulator testing. This blocks an unconditional production security acceptance claim.
- Sustained daily operation over multiple days, load/capacity testing and operational alert delivery are not verified. Local daily scheduling is enabled, but the agent session is not a managed always-on hosting service.
- Source grounding verifies saved evidence, not the truth of every publisher claim. Image vision audits can miss errors; human review is required. Searches may return stale pages, which are excluded. No guarantee of global Instagram originality is made.
