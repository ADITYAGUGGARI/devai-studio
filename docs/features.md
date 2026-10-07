# Product feature status

This page distinguishes implemented code from configured or production-ready services. A feature in the implemented column may still require local credentials or human review.

## Implemented

- **API and storage:** FastAPI app factory, API-key-gated endpoints, SQLAlchemy persistence, SQLite local development, and PostgreSQL Compose setup.
- **Web dashboard:** post library and editor, source research tools, daily run status, manual daily trigger, a separate “Research another story” action that skips previously used sources, evidence review, approval flow, and PNG export.
- **Mobile review app:** Expo app organized for reviewing posts against the API. Device packaging and full device walkthrough are still outstanding.
- **Source discovery:** recent source-dated RSS/Atom items from GitHub, Google Developers, OpenAI, Anthropic Claude Code, Codex, MCP, and arXiv; allowlisted bounded page retrieval; and source excerpts saved with generated drafts.
- **Editorial workflow:** 20-day topic rotation across news, tutorials, architecture, tools, and insights; daily run history; URL/title duplication checks; source attribution; and human approval requirement.
- **Carousel generation and assets:** OpenAI-backed grounded eight-slide copy, captions, hashtags, and slide-specific art directions. The editor can explicitly generate eight original AI artwork images, then typeset the exact copy over each image and export 1080 × 1350 PNGs. Artwork generation uses eight image API calls and may incur usage charges.
- **Developer workflow:** linting, formatting, type checks, API tests, web build, Docker Compose, documentation, and CI configuration.

## Required local configuration

- Set `OPENAI_API_KEY` in the root `.env` and restart both API and scheduler to enable AI generation. Never put provider keys in `web/.env`, `mobile/.env`, or `VITE_*` variables.
- Match `ADMIN_API_KEY` in the root `.env` with `VITE_ADMIN_API_KEY` in `web/.env` for local dashboard API requests.
- Start the API and web app for manual use. Start exactly one `make scheduler` process for scheduled discovery. A configured schedule is not evidence that a scheduler is running.
- Instagram account credentials are not needed for local drafting or export.

## Still to build or validate

1. Add versioned database migrations for existing and future installs; current startup table creation does not migrate schemas.
2. Improve source-feed health and candidate-ranking observability; measure the weighted topic schedule against a reviewed editorial sample.
3. Compare full slide copy and angles across manually created drafts, and add source comparisons to the dashboard. Current checks do not search public Instagram posts and cannot guarantee uniqueness.
4. Validate AI artwork quality, text contrast, visual continuity, and image crops on generated carousels and real devices.
5. Add account-grade authentication, authorization, secret management, backups, monitoring, and multi-instance durable scheduler coordination before public deployment.
6. For live Instagram publishing, host approved JPEG media, bind uploads to the approved post version, and verify Meta integration, concurrency, and reconciliation with a designated test account. Current PNG export and fake-adapter checks do not establish live publishing readiness.
7. Complete browser interaction and native iOS/Android device validation. Type checks alone do not verify device packaging or usability.
8. Revisit the inherited Expo dependency advisories through an upgrade validated on devices.

## Content review before posting

Check the primary source, dates, every factual claim, examples/code, caption attribution, phone-size readability, and the exported PNGs. Correct or reject unsupported claims. Only publish after the normal human approval step; this repository does not automatically post daily content to Instagram.
