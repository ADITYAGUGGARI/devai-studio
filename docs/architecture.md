# Architecture

`main.py` constructs FastAPI, auth/CORS, persistence and an optional background worker. Imports perform no I/O. The original React shell is retained; feature components manage the topic queue, jobs and review editor. Provider credentials remain server-side.

Models preserve existing post, slide, evidence, audit and daily-run records. Alembic provides a static versioned schema; a compatibility adoption path preserves original SQLite installations. Account/session, revision, scheduling, settings and usage tables extend the original models; `topics`, `jobs` and `media_assets` provide persistent workflow state. PostgreSQL is the default local and production persistence; isolated SQLite tests remain supported. Worker processes share the database and asset volumes.

Research gathers relevant dated official-feed entries, retrieves allowlisted bounded source text and queues evidence-backed candidates. Ranking combines freshness and engineering value. Manual evidence requires explicit human verification. Every topic requires version-bound reviewer approval before generation, including automatic selection. Account cookies protect the web dashboard; native sessions use SecureStore. Generation uses prior angles and checks full-copy similarity, then audits claim support with saved-source quotations before persistence.

Real provider web search uses consulted source URLs and bounded allowlisted retrieval; unverified or stale evidence is excluded and failure diagnostics are retained. HTTP handlers enqueue jobs. Workers use conditional updates, unique active keys, expiring leases and heartbeat renewal. Results are saved before later steps, making image retries resumable. Editing and approval are blocked during a post's active jobs. Content/version checks prevent stale generation writes. A separate worker CLI supports API deployments with the embedded worker disabled.

Artwork is entirely image-model composed. Complete source-backed slide text is sent with each distinct visual brief. Pillow only validates, resizes and converts. A vision model transcribes the result independently; programmatic comparison and image hashes supplement its visual checks. Failed reports remain reviewable. There is no fallback programmatic renderer.

Review requires current complete images, validated hashes and source attribution. Publishing rechecks the approved version, reserves it atomically, creates immutable JPEG snapshots and serves them through random media tokens. Meta receives only those snapshots. Unknown outcomes are locked for human reconciliation; publication has no automatic retries.

See [workflow](workflow.md) for configuration, operational guarantees and limits.
