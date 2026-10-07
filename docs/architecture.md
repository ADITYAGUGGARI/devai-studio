# Architecture

`main.py` constructs FastAPI, auth/CORS, persistence and an optional background worker. Imports perform no I/O. The original React shell is retained; feature components manage the topic queue, jobs and review editor. Provider credentials remain server-side.

Models preserve existing post, slide, evidence, audit and daily-run records. Additive startup compatibility migrations add native composition, content hashes and validation metadata; `topics`, `jobs` and `media_assets` provide persistent workflow state. SQLite supports local use; Compose uses PostgreSQL. Worker processes share the database and asset volumes.

Research gathers relevant dated official-feed entries, retrieves allowlisted bounded source text and queues evidence-backed candidates. Ranking combines freshness and engineering value. Manual evidence requires an explicit human verification. Generation uses prior angles and checks full-copy similarity, then audits claim support with saved-source quotations before persistence.

HTTP handlers enqueue jobs. Workers use conditional updates, unique active keys, expiring leases and heartbeat renewal. Results are saved before later steps, making image retries resumable. Editing and approval are blocked during a post's active jobs. Content/version checks prevent stale generation writes. A separate worker CLI supports API deployments with the embedded worker disabled.

Artwork is entirely image-model composed. Complete source-backed slide text is sent with each distinct visual brief. Pillow only validates, resizes and converts. A vision model transcribes the result independently; programmatic comparison and image hashes supplement its visual checks. Failed reports remain reviewable. There is no fallback programmatic renderer.

Review requires current complete images, validated hashes and source attribution. Publishing rechecks the approved version, reserves it atomically, creates immutable JPEG snapshots and serves them through random media tokens. Meta receives only those snapshots. Unknown outcomes are locked for human reconciliation; publication has no automatic retries.

See [workflow](workflow.md) for configuration, operational guarantees and limits.
