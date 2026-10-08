# Existing product UX audit

Audit snapshot: Git commit `036fb71a24c203800fb246c3e946c35c8b7dc4ae` on main, inspected 2026-10-08. Repository: https://github.com/ADITYAGUGGARI/devai-studio. Read README, AGENTS, product/features/architecture/workflow, routes, schemas, models, frontend/native components, styles, job/publishing services and mocked browser tests. No application files changed.

Classification “Already implemented” means the concrete code path exists and was traced; it does **not** assert runtime or live-provider success. Pytest dependencies are absent in this workspace, so backend tests were not executed. Existing Playwright tests mock all APIs; neither those source tests nor documentation establish real model/Meta/iOS success. Live feed health, worker operation, native device packaging, image quality and Instagram permissions remain verification gates.

| Feature | Classification | Evidence path | Observed behavior/limit | Recommendation |
|---|---|---|---|---|
| Authentication/onboarding | Not implemented | core/auth.py; web/services/api.ts; mobile/app/App.tsx | Shared development X-API-Key; no account sessions or onboarding | P0: scoped account auth; no provider secrets in client |
| Shell/navigation | Partially implemented | web/app/App.tsx; style.css | Overview/Library useState; narrow sidebar display:none; no URL history | P0: router, mobile navigation fallback and native stacks |
| Home | Partially implemented | App.tsx; DailyRunPanel | Queue/research/library on same page; no distinct task hierarchy | P1: Home tasks and actual aggregate counts |
| Discover/search | Partially implemented | TopicQueue.tsx; routes/workflow.py | Persistent topics and category filter; no search/pagination/save API | P1: DISC-01 and paginated filters |
| Daily research | Already implemented | jobs.py; topics.py; DailyRunPanel; workflow.md | Date/timezone deduplication; default disabled; actual active scheduler requires verification | Preserve historical daily result separately from latest manual refresh |
| Editorial queue | Already implemented | TopicQueue.tsx; models/workflow.py | Persistent selected topic, priority, archive, source review and 6–8 choice | Add accessible focused topic view and field validation |
| Source verification | Partially implemented | verification.py; ArticleEvidence; workflow.py | Saved exact excerpt, AI audit, human manual verification; primary_source not truth verification | P0: precise provenance/claim status and recheck |
| Custom topic/URL | Already implemented | GenerationForm; POST /topics | Manual excerpt required; URL canonicalization/dedup; no arbitrary automatic fetch | Preserve safety; optional URL-only saved idea requires new contract |
| Creative setup | Partially implemented | TopicQueue; GenerateTopicInput | Only slide_count/artwork; no persisted creative preference wizard | New setup draft and capabilities contracts |
| Carousel generation | Already implemented | generation.py; artwork.py; jobs.py | Full AI compositions, validation, partial asset reuse; runtime model quality unverified | Preserve full composition and 1080×1350 outputs |
| Carousel edit | Partially implemented | PostEditor; routes/posts.py | Explicit Save; copy edits reset validation; no reorder/add/delete/version UI | P0: local-buffer/concurrency; P1 asset structure and history |
| Reel generation | Not implemented | All routes/models inspected; no Reel schema/renderer | Storyboard concepts in prior designs have no matching backend | P1: script/scene/audio/render/MP4 validation contracts |
| Reel editor | Not implemented | mobile/App.tsx; web/features/posts | No timeline/player/audio/subtitle editor | Dedicated desktop timeline and iOS scenes/forms |
| Captions/hashtags | Partially implemented | Post.caption; PostEditor | Caption edit and source citation gate; hashtags unstructured text | Separate format captions and limit validation |
| Preview | Partially implemented | SlidePreview.tsx; mobile/App.tsx | Web actual image blob; mobile textual simulated slide | P0 native actual asset review; no approve-only-text preview |
| Review/approval | Already implemented | routes/posts.py; validate_ready; test_approval.py | Version transitions and invalidation; post-level carousel only | Preserve guard; extend independent format approval and persisted checklist |
| Revision requests | Partially implemented | POST /posts/{id}/reject | Rejected state exists; no structured feedback/target | Record request without automatic AI regeneration |
| Publish immediately | Requires verification | publishing.py; managed_publishing.py; instagram.py | Adapter/snapshot locks exist; live Meta/media reachability unverified | Design explicit account/version confirmation before job |
| Post scheduling/calendar | Not implemented | config contains DAILY_HOUR for research only | Research schedule is not Instagram schedule | New publication reservation/scheduler |
| Instagram connection | Partially implemented | workflow/config; env credentials | One server configured account; no OAuth/settings UI/account discovery | New OAuth and permission test; do not infer Connected from boolean |
| Content library | Partially implemented | PostLibrary.tsx; GET /posts | All-post listing; no query/filter/archive/delete/duplicate lifecycle | New paginated library and retention contracts |
| Activity/jobs | Already implemented | JobPanel; jobs.py; GET /jobs | Database jobs/leases/retry/backoff; last 100; no cancel endpoint or public heartbeat | Preserve no-blind-publish-retry; add health/cancel/pagination |
| Notifications | Not implemented | No notification/push records or provider in code | No durable inbox/native opt-in | New deduplicated server event delivery |
| Analytics | Not implemented | No metric routes/models | Earlier chart mockups use unsupported fabricated numbers | Only capability-supported metrics; provenance and coverage |
| Settings/providers | Partially implemented | GET /workflow/config; Settings env | Read-only config booleans; no CRUD/provider tests/account profile | Server-only vault and connection testing |
| Security/workspace | Not implemented | Shared admin key auth | No actors, roles, tenants, security sessions or member management | P0 auth/access; personal workspace plus explicit collaborator roles |
| Offline/recovery | Partially implemented | request() generic Error; query polling | Durable jobs recover server-side; no local buffer/conflict/offline UX | P0 protected draft cache and CAS writes |
| Native iOS | Partially implemented | mobile/src/app/App.tsx | Single scroll view; API-key entry; text preview; manual refresh | Native navigation, actual assets, accessibility and device QA |
| Accessibility/responsive | Partially implemented | labels/aria in queue; style.css; native Pressable | Some semantic labels; no verified WCAG suite; web nav disappears | P0 accessible navigation and actual review; see test plan |
| Cross-device continuity | Proposed enhancement | Persistent Post/Job; no revision precondition on edits | Server jobs shared; client may overwrite/change slide and lose unsaved fields | P0 revision-checked autosave and explicit conflict resolution |
| Billing/team expansion | Proposed enhancement | No pricing/billing integration | Earlier design included imaginary subscription prices and broad team features | No billing UI in approved scope; owner/editor/reviewer only; business model deferred |

## Critical findings
1. Global busy disables unrelated navigation/actions while one operation runs; replace with per-entity locks and scoped action status.
2. Switching selected slide resets fields from server; unsaved fields can disappear. Explicit Save is not autosave; no leave guard.
3. Post fields initialize from props and do not consistently reconcile refreshed server revision. PATCH accepts no expected version, so concurrent clients can overwrite changes.
4. On narrow web layouts the only navigation sidebar disappears with no replacement. Refresh cannot preserve selected post because selection is local state.
5. Native review shows textual fields, not actual model lettering/diagrams. Approval must require inspection of actual media.
6. Publish button directly queues without a final account/version/caption confirmation. Backend protects approval, but explicit UX review must be added.
7. A source identity label and AI quote match must not become “verified facts” without human review. Old design boards use overconfident source counts.
8. No production account isolation. Development API key is embedded in web build and cannot serve as public account authentication.
9. No cancellation route/public heartbeat; cannot render functional Cancel or truthful server-stalled state until contracts exist.
10. docs/product.md says exact eight generator while current GenerateTopicInput accepts 6–8. Preserve actual current schema; flag documentation conflict for engineering.

## Prior design review
Inspected Design 01 warm shell, 02 dashboard, 03 Discover/research, 04 creation setup, 05 carousel editor, 06 Reel editor, 07 review/publish, 08 library/activity, 09 analytics, 10 settings, corrected 11 additional states, plus revised Design 01A. Retrieved named PNG references; file mapping is in audit/reference-manifest.json. Preserve forest sidebar, cream surfaces, peach warmth, calm hierarchy, editorial headlines, roomy rows and consistent desktop/iOS brand. Supersede purple status/buttons, fully white surfaces, varying token hex values, excessive tiny multi-screen boards, unsupported news sample claims and invented billing/analytics. No generated model-release claim in a reference is adopted as product fixture fact.

Correct prior carousel Layout/Style controls: user edits intended copy and freeform art brief; generated full composition must be regenerated and validated. No promise of immediate text-layer changes. Correct Reel durations: target 30–40 seconds only, not invented 15/60 choices. Correct combined approval: each format independently approves and independently publishes; two outputs never treated as a single Instagram post. Correct retries: unknown Instagram outcome never displays generic Retry. Correct delete: reversible Trash before explicit permanent purge.
