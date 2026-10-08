# Proposed route and native destination specification

These routes describe the intended product. Current web code has only local Overview/Library state and no router. UUID IDs must be validated and workspace-scoped. `:format` is carousel or reel; all unknown enums → Not found. Query values are encoded and parsed against allowlists.

| ID | Web route | iOS destination | Guard | Parent | Purpose |
|---|---|---|---|---|---|
| AUTH-01 | /sign-in | DevAI/AUTH-01 | Public | Public | Authenticate without exposing provider credentials |
| AUTH-02 | /sign-in/verify | DevAI/AUTH-02 | Public | AUTH-01 | Confirm a time-limited email code |
| ONB-01 | /onboarding | DevAI/ONB-01 | Authenticated; no workspace required | AUTH-02 | Set language, timezone and research preferences |
| HOME-01 | /home | DevAI/HOME-01 | Authenticated + workspace scope | Home tab | Choose the next useful editorial action |
| DISC-01 | /discover | DevAI/DISC-01 | Authenticated + workspace scope | Discover tab | Browse fresh source-backed topics |
| QUEUE-01 | /discover/queue | DevAI/QUEUE-01 | Authenticated + workspace scope | DISC-01 | Prioritize available topics for creation |
| TOPIC-01 | /topics/:topicId | DevAI/TOPIC-01 | Authenticated + workspace scope | DISC-01 | Understand a topic before committing effort |
| SOURCE-01 | /topics/:topicId/sources | DevAI/SOURCE-01 | Authenticated + workspace scope | TOPIC-01 | Inspect saved evidence and primary references |
| CLAIM-01 | /content/:contentId/claims | DevAI/CLAIM-01 | Authenticated + workspace scope | TOPIC-01 | Resolve unsupported factual claims |
| IMPORT-01 | /topics/new | DevAI/IMPORT-01 | Authenticated + workspace scope | DISC-01 | Add a custom idea with attributable evidence |
| CREATE-01 | /create?topic=:topicId | DevAI/CREATE-01 | Authenticated + workspace scope | TOPIC-01 | Choose an output supported by configured providers |
| CREATE-02 | /create/:setupId/configure | DevAI/CREATE-02 | Authenticated + workspace scope | CREATE-01 | Define audience and creative intent |
| CREATE-03 | /create/:setupId/review | DevAI/CREATE-03 | Authenticated + workspace scope | CREATE-02 | Authorize generation with transparent effort |
| GEN-01 | /content/:contentId/generation | DevAI/GEN-01 | Authenticated + workspace scope | LIB-02 | Monitor each output without blocking navigation |
| CAR-01 | /content/:contentId/carousel | DevAI/CAR-01 | Authenticated + workspace scope | LIB-02 | Edit copy and regenerate complete compositions |
| CAR-02 | /content/:contentId/carousel/slides/:slideId | DevAI/CAR-02 | Authenticated + workspace scope | CAR-01 | Edit one slide with a focused native form |
| CAR-03 | /content/:contentId/carousel/regenerate/:slideId | DevAI/CAR-03 | Authenticated + workspace scope | CAR-01 | Create a new composition while preserving old assets |
| VER-01 | /content/:contentId/versions | DevAI/VER-01 | Authenticated + workspace scope | Invoking editor | Compare and restore a saved version safely |
| REEL-01 | /content/:contentId/reel | DevAI/REEL-01 | Authenticated + workspace scope | LIB-02 | Edit a real vertical video with explicit render status |
| REEL-02 | /content/:contentId/reel/script | DevAI/REEL-02 | Authenticated + workspace scope | REEL-01 | Edit spoken copy and estimate timing |
| REEL-03 | /content/:contentId/reel/scenes | DevAI/REEL-03 | Authenticated + workspace scope | REEL-01 | Manage scenes using touch-friendly cards |
| REEL-04 | /content/:contentId/reel/scenes/:sceneId | DevAI/REEL-04 | Authenticated + workspace scope | REEL-03 | Adjust one scene and preserve validated assets |
| REEL-05 | /content/:contentId/reel/audio | DevAI/REEL-05 | Authenticated + workspace scope | REEL-01 | Configure narration and licensed music |
| REEL-06 | /content/:contentId/reel/subtitles | DevAI/REEL-06 | Authenticated + workspace scope | REEL-01 | Correct transcript and timing |
| CAP-01 | /content/:contentId/caption/:format | DevAI/CAP-01 | Authenticated + workspace scope | Invoking editor | Write a grounded caption for the chosen format |
| PRE-01 | /content/:contentId/preview/carousel | DevAI/PRE-01 | Authenticated + workspace scope | Invoking screen | Inspect every final image at publication dimensions |
| PRE-02 | /content/:contentId/preview/reel | DevAI/PRE-02 | Authenticated + workspace scope | Invoking screen | Review only the selected rendered MP4 |
| REVIEW-01 | /review | DevAI/REVIEW-01 | Authenticated + workspace scope | Content tab | Find each format needing a decision |
| REVIEW-02 | /review/:contentId/:format | DevAI/REVIEW-02 | Authenticated + workspace scope | REVIEW-01 | Approve exact inspected assets and evidence |
| REVIEW-03 | /review/:contentId/:format/changes | DevAI/REVIEW-03 | Authenticated + workspace scope | REVIEW-02 | Record actionable feedback without triggering paid generation |
| PUB-01 | /content/:contentId/publish/:format | DevAI/PUB-01 | Authenticated + workspace scope | Approved output | Authorize a specific account, version and time |
| PUB-02 | /publications/:publicationId | DevAI/PUB-02 | Authenticated + workspace scope | LIB-02 | Understand confirmed and uncertain publication outcomes |
| PUB-03 | /publications/:publicationId/reconcile | DevAI/PUB-03 | Authenticated + workspace scope | PUB-02 | Record externally verified publication result |
| CAL-01 | /calendar | DevAI/CAL-01 | Authenticated + workspace scope | Content tab | Manage authorized upcoming publications |
| LIB-01 | /content | DevAI/LIB-01 | Authenticated + workspace scope | Content tab | Find and manage all work by lifecycle and format |
| LIB-02 | /content/:contentId | DevAI/LIB-02 | Authenticated + workspace scope | LIB-01 | See related outputs and act on each independently |
| TRASH-01 | /content/trash | DevAI/TRASH-01 | Authenticated + workspace scope | LIB-01 | Recover work within the retention window |
| ACT-01 | /activity | DevAI/ACT-01 | Authenticated + workspace scope | Activity tab | Monitor jobs and their durable history |
| ACT-02 | /activity/jobs/:jobId | DevAI/ACT-02 | Authenticated + workspace scope | ACT-01 | Inspect real progress and recover safely |
| NOT-01 | /notifications | DevAI/NOT-01 | Authenticated + workspace scope | Invoking tab | Follow meaningful workflow events |
| ANA-01 | /analytics | DevAI/ANA-01 | Authenticated + workspace scope | Home tab | Interpret available Instagram performance honestly |
| ANA-02 | /analytics/posts/:publicationId | DevAI/ANA-02 | Authenticated + workspace scope | ANA-01 | Inspect post-level metrics and their definitions |
| ANA-03 | /analytics/compare | DevAI/ANA-03 | Authenticated + workspace scope | ANA-01 | Compare compatible metrics over comparable periods |
| SET-01 | /settings | DevAI/SET-01 | Authenticated + workspace scope | Settings tab | Find profile, workflow and integration preferences |
| SET-02 | /settings/profile | DevAI/SET-02 | Authenticated + workspace scope | SET-01 | Manage identity, language and timezone |
| SET-03 | /settings/research | DevAI/SET-03 | Authenticated + workspace scope | SET-01 | Configure durable daily discovery |
| SET-04 | /settings/providers | DevAI/SET-04 | Authenticated + workspace scope | SET-01 | Configure capabilities without exposing secrets |
| SET-05 | /settings/providers/:providerId | DevAI/SET-05 | Authenticated + workspace scope | SET-04 | Test credentials before enabling a capability |
| SET-06 | /settings/instagram | DevAI/SET-06 | Authenticated + workspace scope | SET-01 | Connect eligible publishing accounts |
| SET-07 | /settings/instagram/:accountId | DevAI/SET-07 | Authenticated + workspace scope | SET-06 | Inspect eligibility and recover access |
| SET-08 | /settings/notifications | DevAI/SET-08 | Authenticated + workspace scope | SET-01 | Choose useful in-app and push notices |
| SET-09 | /settings/security | DevAI/SET-09 | Authenticated + workspace scope | SET-01 | Manage active devices and account protection |
| SET-10 | /settings/workspace | DevAI/SET-10 | Authenticated + workspace scope | SET-01 | Manage the personal studio and limited collaborators |
| SET-11 | /settings/data | DevAI/SET-11 | Authenticated + workspace scope | SET-01 | Export data and request account removal |
| HELP-01 | /help | DevAI/HELP-01 | Authenticated + workspace scope | SET-11 | Resolve configuration and workflow problems |
| SYS-01 | /session-recovery | DevAI/SYS-01 | Authenticated + workspace scope | Original destination | Recover authentication without losing buffered work |
| SYS-02 | /not-found | DevAI/SYS-02 | Authenticated + workspace scope | Original destination | Recover from deleted or unknown destinations |
| GEN-02 | /content/:contentId/reel/generation | DevAI/GEN-02 | Authenticated + workspace scope | LIB-02 | Track actual Reel milestones until validated MP4 |

## History, redirects and deep links
`/` → `/home` when signed in, otherwise `/sign-in?returnTo=<safe local path>`. `/library` → `/content`, `/overview` → `/home` as migration aliases. No arbitrary external returnTo. Authenticated sign-in → Home, except pending reauthentication. Onboarding incomplete → onboarding with intended destination retained. Unknown/deleted/inaccessible resource uses SYS-02; do not reveal foreign-workspace existence. Do not redirect permission errors into an authentication loop.

Native universal links on the configured app origin map these same resource routes into five independent tab stacks. Home, Discover, Content, Activity, Settings tabs always remain available. Review is a prominent Content segment and Home task entry; Analytics is a Settings destination and Home shortcut. Content editors open as a full-screen modal navigation stack with Done; nested forms use native push and Back. Tab stacks preserve scroll and search. Deep links authenticate then validate access and server status before presenting. Malformed links fall back Home with “This link is no longer available.”

List search, filters, tab, sort and cursor are encoded in URL query. Pagination cursor is opaque; no database IDs guessed. Preview is routable; opening from editor captures return location, scroll, selected stable asset ID and playhead. Browser reload fetches authoritative snapshot, restores local unsynced buffer only for same account/entity/revision. Browser Back and iOS back gesture use the same unsaved policy; neither silently loses work. Overlay close returns to invoker; direct-linked overlay closes to parent.

| DISC-02 | /discover/research | DevAI/DISC-02 | Authenticatedworkspace | DISC-01 | Allresearchrunsandcoverage |

Researchrunselection /discover?run=:runId&disposition=all;runIdopaqueUUIDguard,denied/missingrunSYS-02,neverfetchanotherworkspace.
