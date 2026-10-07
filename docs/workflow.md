# Content workflow and operations

The React dashboard retains its original shell, colors, navigation, library and editor. The queue and job controls extend those screens. API endpoints require `X-API-Key`, except health and unguessable publishing-media URLs.

## Research and topic selection

1. **Refresh research** enqueues a research job. Official RSS/Atom feeds are checked for relevant, dated entries within 14 days. Source-page retrieval is allowlisted, bounded and redirect-free. Evidence must contain at least 240 readable characters. Queue rows preserve the source URL, publisher, publication/retrieval dates and excerpt.
2. The persistent queue ranks recency and engineering usefulness; priority can be changed from 0–100. Topic selection is persisted across reloads. The upstream `/editorial` API remains compatible and its existing shortlist is migrated into this unified queue. Category filtering, archival/restoration, evidence review and manual selection are available in the dashboard.
3. **Add source to queue** saves a manually supplied excerpt as unverified. A reviewer must explicitly verify its evidence before generating. Manual sources are not automatically fetched, avoiding arbitrary URL requests.
4. Choose 6, 7 or 8 slides and whether to generate images with the copy. Text generation is original developer analysis, with prior editorial angles and full-copy similarity checks. Canonical source URL and title checks prevent reuse. These checks cannot guarantee uniqueness across public Instagram content.
5. An independent model audits factual claims against the saved excerpt; evidence quotes must occur in that excerpt. Failed grounding saves no fabricated draft. A primary-source check and an AI grounding audit are **not** independent proof of the publisher's claims. Human review remains required.

## Complete image composition

Every new slide is a complete image-model composition: imagery, diagrams, lettering, typography and copy. There are no layout presets, CSS/SVG compositions, drawing operations, or local text overlays in the artwork path. Pillow only decodes images, validates dimensions, resizes and converts formats. The default image request is `gpt-image-2`, medium quality, 1088 × 1360 (4:5); it is resized without cropping to 1080 × 1350.

A vision model transcribes each image without receiving the expected script. The server compares its transcription with the stored headline/body, allowing whitespace and typographic punctuation normalization. It also checks legibility, clipping, additional factual text, dimensions, and duplicate image bytes. Reports and image/content hashes are persisted per slide. Vision checks can miss errors and are not a substitute for inspecting every image.

Each failed slide receives a second generation pass with diagnostic feedback by default. If it still fails, the image and diagnostics remain visible and approval is blocked. **Regenerate selected slide** requests only that slide. Regeneration invalidates approval. Copy/title edits make affected images stale; stale or legacy overlay images cannot be approved or exported as current content. Existing records and files are preserved; regenerate their images to move to complete composition.

## Background processing and retries

Requests enqueue jobs and return HTTP 202 with the durable job record. `/jobs` and `/jobs/{id}` expose status, step, progress, attempts, retry availability, partial results and safe errors. The dashboard polls this state and can open a draft before all images finish. Closing the browser does not stop a job.

The API runs a background worker by default (`BACKGROUND_WORKER_ENABLED=true`). For a dedicated worker, disable that setting in the API and start `make worker`, or use Compose's `workers` profile. Workers must share the database, artwork directory and publishing-media directory. Atomic claims, unique active keys, leases and periodic heartbeats prevent concurrent work on one job. Expired non-publishing leases are reclaimed; current validated slides are reused on retry. Post changes are blocked during its active jobs, and version checks discard stale generation output. Jobs retry transient provider connection errors, 429s and 5xx responses up to three times, with 30/60-second backoff. Billing, missing-key, validation and source-grounding failures require correction and a manual retry. Retries may repeat a provider call that succeeded externally before the process crashed but was not saved locally.

Set `DAILY_ENABLED=true` to let the API/worker enqueue persistent daily research at or after `DAILY_HOUR` in `DAILY_TIMEZONE`. Alternatively run `make scheduler`; it enqueues daily jobs for a worker to execute. Date/timezone schedule keys survive scheduler restarts. Daily discovery refreshes the queue without generating posts by default, preserving the upstream topic-first workflow. Select a topic explicitly in the dashboard to generate it. Optionally set `DAILY_GENERATE_CAROUSEL=true` to create a daily draft and complete images from the highest-priority available topic in the editorial category rotation, falling back to other categories. An already completed daily run is preserved. `Refresh more topics` adds fresh candidates; the legacy `/research/daily/regenerate` endpoint remains available for an explicit additional draft pipeline. This is application scheduling, not a ChatGPT automation or an installed OS service. The schedule is disabled by default; keep at least one API/worker process running to execute jobs.

## Approval, export and publishing

Submit the post for review, inspect the complete source excerpt, audit, code, caption and all images, then explicitly approve. Approval requires six to eight current AI-native images, passing validation/integrity checks, saved source evidence and its exact citation in the caption. Every edit or image regeneration resets approval. The ZIP export contains the exact model-generated PNGs, `caption.txt`, `sources.json` and `review.json`, including the post version and validation reports.

Publishing requires:

- `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_ACCOUNT_ID` and a supported `META_GRAPH_VERSION`, with the Facebook Login Instagram professional-account publishing permissions configured in Meta.
- `PUBLIC_MEDIA_BASE_URL`: the public HTTPS origin (or reverse-proxy prefix) of this API, reachable by Meta. Localhost alone cannot provide publishing media.
- Persistent shared `PUBLISH_MEDIA_DIR` and `CAROUSEL_ARTWORK_DIR` storage.

**Publish approved carousel to Instagram** queues a publish job for the exact approved version. The worker rechecks approval, source citation, content/image hashes and images; atomically reserves that version; converts its images to immutable JPEG snapshots; and stores unguessable media tokens and checksums. `/media/{token}.jpg` serves only those prepared snapshots. Arbitrary external image URLs cannot replace approved images. The Meta adapter creates carousel children and parent, waits for readiness, then performs the final publish call once. Publishing does not run automatically after approval.

Publishing failures and interrupted workers are never blindly retried. When the outcome is uncertain, the post remains locked in `publishing`. A reviewer must check Meta/the Instagram account and use **Reconcile Instagram outcome** to record a confirmed media ID or confirm non-publication with notes. Confirmed non-publication returns the post to draft, requiring review/approval before a new attempt.

## Validation performed and remaining verification

Backend regression tests mock provider/Meta calls and use isolated databases and synthetic image fixtures. They cover the topic-to-image workflow, provenance, approval invalidation, validation failures, resumable retries, lease recovery, publishing snapshots, uncertainty and reconciliation. They never spend credits or publish real content. `npm run test:e2e` additionally runs four browser regression tests with all API calls mocked (install Chromium with `npx playwright install chromium`, or use `PLAYWRIGHT_CHROMIUM_CHANNEL=chrome` with installed Chrome). CI runs these browser tests. `make check` runs the backend tests, Ruff, ESLint, Prettier, web/mobile type checks and the web production build.

Live feed health varies. OpenAI billing/model access and complete-image visual quality need a configured account and a reviewed real carousel. Meta app permissions, public media retrieval and real publishing need a designated test account. Public deployment still requires account-grade authentication, backups, storage lifecycle controls and monitoring. The inherited mobile app needs native device verification.
