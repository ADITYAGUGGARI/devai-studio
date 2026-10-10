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

## UX design handoff available

Revision4 implementation now includes persisted workspace research schedules across web and native iOS, once-per-local-day reservations with DST handling, frozen research categories, optimistic concurrency recovery and real Run now background jobs. Native session storage is isolated per backend. FFmpeg supports active-process cancellation and preserves previous renders. Full revised Reel orchestration/editing, independent output approvals and the complete screen/control matrix remain implementation work; see the current checkpoint in `IMPLEMENTATION_STATUS.md`.

[Revision 4 desktop and native iOS design handoff](ux/devai-studio-v4/README.md) defines the complete intended product and dependency-aware implementation plan. The package includes ranked rolling-24-hour developer AI research, autonomous varied carousel/Reel artwork, independent approvals, explicitly authorized publication, recovery states, and the remaining workflows. Publication of the design package does not mark proposed backend or client capabilities as implemented or verified. See its [implementation roadmap](ux/devai-studio-v4/handoff/roadmap.md) and [QA limitations](ux/devai-studio-v4/qa/review.md).

Account roles/sessions, PostgreSQL migration/adoption, backups with restore verification, usage/monitoring, publishing schedules, version restore and connected browser tests are implemented. See IMPLEMENTATION_STATUS.md for current evidence.

The workflow UX acceptance audit added persistent background-task feedback, completion/recovery actions, unsaved-edit protection, safe cross-section saves, configuration guards and expanded connected account/settings verification. See [workflow acceptance](WORKFLOW_ACCEPTANCE.md) for the tested journeys and remaining external/native verification.
