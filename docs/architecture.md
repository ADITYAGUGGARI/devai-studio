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

Tables are `posts`, `slides`, `source_candidates`, `audit`, and `publish_attempts`. Existing string-valued versions and padded positions are retained to avoid an implicit migration. Native development uses SQLite; Docker uses PostgreSQL. Schema creation is not a migration system.

## Content paths

- Manual creation stores editable copy and ordered slides.
- Discovery parses configured feeds and returns source links and feed errors.
- Scaffolds contain eight placeholder slides explicitly requiring verification.
- AI generation uses the supplied excerpt, validates eight-slide output, retains attribution, and saves a draft.
- Export renders saved slides into 1080 × 1350 PNGs and a caption file in a ZIP. Fonts support OS paths, overrides, and a Pillow fallback. The browser preview approximates the exported layout.

Originality currently means URL deduplication during ingestion plus title similarity at generation time. Manual drafts can overlap; generated source URLs are not yet in a unified history index. These checks are not plagiarism detection.

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

One explicit process checks the configured local hour every minute, including catch-up after a late startup. Its last-run date is in memory; source identities persist. Durable run records, leases, retry policy, ranking, complete draft generation, and automatic export belong to the next milestone.
