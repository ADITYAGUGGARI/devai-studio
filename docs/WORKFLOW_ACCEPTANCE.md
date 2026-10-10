# Workflow acceptance — October 7, 2026

This audit reused the existing web/backend/native application and an AI-generated interaction reference. It does not establish unrestricted provider availability, successful Instagram publication, or full native automated acceptance.

## Interaction changes

- Research/search/generation starts durable work without forcing a screen change. A task strip stays visible across web workspaces, with real progress, retry timing, completion links and failure diagnostics. Activity separates active, attention and historical jobs.
- Successful mutations show dismissible feedback; request validation identifies invalid fields and preserves manual input. Independent query refreshes run together.
- Unsaved copy/slide edits survive cancellation of navigation. Slide switching, leaving the editor and signing out require an explicit discard when necessary; browser unload is guarded. Caption saves preserve pending slide changes. Unsaved edits block submission, artwork regeneration, version restoration and export.
- Publishing and scheduling explain missing integration configuration and disable unavailable actions. Export stays available. Viewer draft creation and source entry are disabled; server role enforcement remains authoritative.

## Verification matrix

| Journey                                                                        | Evidence                                                                                              | Scope / limitation                                                                                                          |
| ------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Sign-in, session reload, sign-out, unauthorized access                         | Connected Playwright and PostgreSQL backend tests                                                     | Real FastAPI sessions in isolated schema                                                                                    |
| Daily/manual discovery, ranking, deduplication, evidence warnings              | PostgreSQL service tests; actual browser research job `758b45df-a41e-4351-a005-6fc43d2610af`          | Live job completed with warnings, added zero duplicates; OpenAI News HTTP 403 prevented readable evidence for three stories |
| Source entry, verification, topic approval and selection                       | Connected browser journey; API tests; manual-input validation browser test                            | Live provider drafting is not triggered by ordinary tests                                                                   |
| Copy and full image generation, validation and individual regeneration         | Existing real eight-image provider artifact; backend workflow/recovery tests                          | Previously live-tested provider result is reused; no new paid image generation in this audit                                |
| Background navigation, completion, retry and publishing reconciliation         | Browser transition/recovery tests; PostgreSQL worker recovery tests                                   | External calls isolated; uncertain publication has no blind retry                                                           |
| Editor copy/slide saves, unsaved edits, version restore, approval invalidation | Real connected browser journey, keyboard/modal regressions, backend approval tests                    | Caption save preserves pending slide edits; saved-version approval remains mandatory                                        |
| Eight-image ZIP export and approval                                            | Connected browser with actual generated PNGs                                                          | No real Instagram post is sent                                                                                              |
| Scheduling and cancellation                                                    | Browser API-contract journey; PostgreSQL scheduling/dispatch/invalidation tests                       | Official Meta credentials and public HTTPS media origin are absent locally                                                  |
| Settings persistence and account provisioning                                  | Connected browser journey                                                                             | Test settings/users only, separate schema                                                                                   |
| Viewer permissions                                                             | Connected browser plus API role tests                                                                 | Unavailable mutation buttons disabled; backend rejects unauthorized writes                                                  |
| Responsive web and accessibility                                               | Axe in connected journeys; desktop/phone screenshots; real local background navigation overflow check | Platform-specific visual regression snapshots                                                                               |
| iOS                                                                            | Running Expo Go Today screen visually inspected; mobile TypeScript checked                            | Maestro CLI is not installed; native automated acceptance not run. This audit makes no native code changes                  |

## Commands and results

- `make check`: 107 backend tests, Ruff, ESLint, formatting, web/mobile TypeScript and production web build.
- `make test-postgres`: 107 passed using disposable PostgreSQL schemas.
- `npm run test:e2e`: 17 passed; API fixtures are isolated test doubles.
- `npm run test:e2e:connected` with `LIVE_CAROUSEL_FIXTURE`: 3 passed against actual FastAPI/PostgreSQL, including real image export and version recovery.
- Local browser research acceptance: completed with source warnings while remaining in Library; task strip and completion state visually verified at desktop and phone widths.

The local worker, daily setting and OpenAI configuration report enabled/configured. Configuration alone does not establish sustained daily scheduling; multi-day observation remains required. Instagram and public media configuration report unavailable. Do not claim all production or native journeys have passed.
