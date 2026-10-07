# Roadmap

## Implemented in the current workflow

- Persistent prioritized research queue and manual topic selection.
- Complete capped RSS/Atom parsing, full feed evidence, publisher-only redirects and grouped source diagnostics with explicit partial-success status and topic counts.
- Source-grounded 6–8-slide writing with citations and independent evidence audit.
- Verbatim evidence audits with strict schemas, bounded quote-format re-audits and persisted claim-level failure diagnostics.
- Complete AI-native per-slide composition, validation diagnostics and individual regeneration.
- Durable background jobs, progress, transient retries and interrupted-job recovery.
- Human review/approval, version invalidation, metadata-rich export and managed Instagram publishing.

## Verification and deployment milestones remaining

1. Review a real generated carousel across all supported image/vision configurations; measure lettering errors and validation false negatives.
2. Validate public JPEG retrieval, Meta app permissions, container processing and publication with a designated Instagram test account.
3. Validate sustained daily operation and feed health over multiple days; add ranking quality feedback from reviewed posts. OpenAI article pages currently return HTTP 403 to the local server; short feed summaries remain excluded rather than treated as sufficient evidence.
4. Add account-grade authentication and authorization before exposing the dashboard beyond local use.
5. Add versioned production migration tooling, backups, monitoring, asset retention/cleanup and load testing of concurrent PostgreSQL workers.
6. Validate the mobile review app on iOS/Android and upgrade inherited Expo dependencies with device tests.
7. Expand originality comparisons with accessible external content; never claim uniqueness across all Instagram accounts.
