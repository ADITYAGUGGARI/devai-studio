# Architecture

## Decision: retain three applications in one repository

FastAPI, React/Vite, and Expo remain independent applications. The backend is an installable `api/src/devai` package; clients have feature-oriented source directories. The root owns common tooling and documentation. Generated OpenAPI contracts can replace the small duplicated client types later.

## Request and storage flow

```text
Web / mobile -> API-key dependency -> route + input schema
                                     -> transaction / service
                                     -> model or external adapter
```

`create_app` accepts settings and an optional engine. Routers obtain its session factory through a dependency. Imports do not open database connections or create tables; app lifespan initializes the development schema. Tests inject isolated SQLite databases. The scheduler constructs its own engine without importing the HTTP app.

Tables are `posts`, `slides`, `source_candidates`, `article_evidence`, `daily_runs`, `audit`, and `publish_attempts`. Existing string-valued versions and padded positions are retained to avoid an implicit migration. The evidence and daily-run tables are added by development schema creation. Native development uses SQLite; Docker uses PostgreSQL. Schema creation is not a migration system.

## Content paths

- Manual creation stores editable copy and ordered slides.
- Discovery parses configured feeds and returns source links and feed errors.
- Scaffolds contain eight placeholder slides explicitly requiring verification.
- AI generation uses the supplied excerpt, validates eight-slide output, retains attribution, and saves a draft.
- The editor can request one AI-generated image per slide from its slide-specific art direction. Exact headline/body text is overlaid locally for legibility. Artwork files are stored under `.local-data/carousel-artwork` and slide rows retain their paths. Regenerating artwork increments the post version and returns it to draft so approval must happen afterward.
- Export renders saved slides and optional artwork into 1080 × 1350 PNGs and a caption file in a ZIP. Fonts support OS paths, overrides, and a Pillow fallback. The browser preview loads the same server-rendered image used for export.

Daily ingestion avoids previously used canonical source URLs, near-duplicate source titles, and recent angles in its generation prompt. Manual and independently generated drafts can still overlap, and public Instagram posts are not searched. These checks are not plagiarism detection or a guarantee of uniqueness.

## Review and publishing

```text
draft / rejected -> pending_review -> approved
                                  -> rejected
approved -> publishing -> published
                     -> needs_reconciliation (attempt; post stays publishing)
editable content + edit -> draft, increment version
```

The exact publishing route precedes the generic review-action route. It checks credentials, approval, and image count, then atomically reserves the version. The adapter creates child containers, waits for readiness, creates a carousel container, and performs one final publish call. Owned HTTP clients are closed. Errors record their type rather than possibly credential-bearing provider details.

Image URLs are caller-supplied; they are not yet bound to approved slides. Production publishing needs managed media, account authentication, and concurrent edit/publish tests on PostgreSQL. No live Meta verification is claimed.

## Scheduling

One explicit process checks the configured local hour every minute, including catch-up after a late startup. A unique daily-run record persists its claim, result, and up-to-three retries. RSS candidates are ranked for recency and editorial-topic fit; one source-backed eight-slide carousel is generated and rendered from the saved slide copy. Human review and image export are still required. The dashboard can start the same daily operation manually.

AI artwork is a separate, explicit editor action so eight image-generation requests do not happen unexpectedly during daily text generation. The server uses `OPENAI_IMAGE_MODEL` (default `gpt-image-2`); API billing and model access are required. Docker stores artwork in its named `carousel_artwork` volume.
