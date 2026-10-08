# Roadmap

## Implemented in the current workflow

- AI-assisted UX wireframe, focused mobile Today/Discover/Library/Publishing navigation, separate source/job screens and sectioned review; web workspaces separated by purpose.
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
4. Complete iOS simulator/device acceptance with full Xcode and run the prepared Maestro flow.
5. Resolve inherited native dependency security advisories with a supported Expo SDK migration and simulator regression.
6. Verify TLS ingress, operational alerts, storage retention and concurrent-worker capacity before public deployment.
7. Expand originality comparisons with accessible external content; never claim uniqueness across all Instagram accounts.

Account roles/sessions, PostgreSQL migration/adoption, backups with restore verification, usage/monitoring, publishing schedules, version restore and connected browser tests are implemented. See IMPLEMENTATION_STATUS.md for current evidence.
