# TOPIC-01 — Topic overview

Purpose: Understand a topic before committing effort. Web route `/topics/:topicId`; iOS destination `DevAI/TOPIC-01`. Parent: DISC-01; preserve invoker on reusable editor/preview.

## Composition

Desktop: 760px reading column, 320px source rail, sticky Create content. At1440px use232px sidebar,32px page gutter and24px gaps; dedicated editors suppress ordinary shell content navigation but retain Done, entity title and Activity status.

iOS: Summary/Sources/Claims segmented control; bottom Create content above safe area. Physical viewport390×844 with top safe area47 and bottom34; content scrolls between navigation and fixed actions. Body17pt,44pt targets. Native child editor hides tab bar and uses Done/Back; root destinations keep five tabs. Long form continuation is scrolling content, not a tall fictional phone.

Content and focus order: Topic summary → Sources → Claims → Editorial angle → Create content. Read boundary: GET /topics. Only the contracts below mutate. All IDs are stable, not row indices.

## Controls — authoritative revision 3

| ID/control | Preconditions/trigger | Action and success | Operation/request | Exact next destination | Failure and recovery |
|---|---|---|---|---|---|
|TOPIC-01-I01 topic-tabs|Read permission for requested entity; public routes exempt; Click/Enter/Space or native tap; drag has Move before/after alternative|Select labeled tab; preserve other panels state; update URL tab parameter; browser Back restores selection; no mutation.|None: local UI/navigation; destination resource read only No payload|/topics/:topicId|Read failure retains last loaded content labeled stale with Retry; denied/missing target opens SYS-02; offline navigation uses cached authorized content. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|TOPIC-01-I02 save-topic|Authenticated workspace and permitted role; Click/Enter/Space or native tap; drag has Move before/after alternative|Toggle Saved with server acknowledgment; no topic status change|PUT /v1/topics/{topicId}/saved {saved:!currentSaved}|Remain on /topics/:topicId with acknowledged revision/state; no implicit publication or navigation|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|TOPIC-01-I03 open-source|Read permission for requested entity; public routes exempt; Click/Enter/Space or native tap; drag has Move before/after alternative|Open canonicalHTTPS externally with noreferrer; cached snapshot remains available if source fails.|None: local UI/navigation; destination resource read only No payload|/topics/:topicId|Read failure retains last loaded content labeled stale with Retry; denied/missing target opens SYS-02; offline navigation uses cached authorized content. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|TOPIC-01-I04 edit-angle|Authenticated workspace and permitted role; Click/Enter/Space or native tap; drag has Move before/after alternative|Save angle; do not rewrite source excerpt|PATCH /v1/topics/{topicId}/angle {expectedRevision,editorialAngle}|Remain on /topics/:topicId with acknowledged revision/state; no implicit publication or navigation|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|TOPIC-01-I05 create|Read permission for requested entity; public routes exempt; Click/Enter/Space or native tap; drag has Move before/after alternative|Open CREATE-01 for selected authorized entity; preserve originating route, tab stack and scroll.|None: local UI/navigation; destination resource read only No payload|CREATE-01|Read failure retains last loaded content labeled stale with Retry; denied/missing target opens SYS-02; offline navigation uses cached authorized content. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|TOPIC-01-I06 open-draft|Read permission for requested entity; public routes exempt; Click/Enter/Space or native tap; drag has Move before/after alternative|Open LIB-02 for selected authorized entity; preserve originating route, tab stack and scroll.|None: local UI/navigation; destination resource read only No payload|LIB-02|Read failure retains last loaded content labeled stale with Retry; denied/missing target opens SYS-02; offline navigation uses cached authorized content. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|

## State and persistence contract

Applicable states: initial, loading, populated, failure, permission_denied, session_expired, offline, reconnecting. Loading reserves actual layout using skeletons for lists, inline spinner only for submitted control; empty list explains scope and offers Clear filters or relevant create action. Do not show an empty screen while loading. Offline exposes cached timestamp, queues only protected text edits, and disables generation, approval and publication with explanation. Session expiry keeps protected local buffer and returns here after authentication. Permission loss immediately removes mutation actions while preserving permitted read view.

Editors save800ms after idle, ordered per entity with expectedRevision. Saved requires ACK; failure retains buffer and Save now.409 displays field-level base/mine/server comparison; accepting server never silently deletes mine. Back/Done with unacknowledged buffer offers Save, Discard local changes, Stay; selecting Save must succeed before leaving. Navigation never cancels durable jobs. Read-only screens have no autosave, draft, or paid action merely because they share components.

Dialogs follow interactions/dialogs.md; per-control triggers and responses are in interactions.json. Native focus enters screen title; web route title receives focus except returning to original invoker. Preview revision is labeled and retained; latest revision refresh cannot silently swap an approved preview.

## Visuals and tests

Desktop `visuals/desktop/TOPIC-01-default.svg`; iOS `visuals/ios/TOPIC-01-default.svg`. Per-control tests: TOPIC-01-AT01, TOPIC-01-AT02, TOPIC-01-AT03, TOPIC-01-AT04, TOPIC-01-AT05, TOPIC-01-AT06. Critical state-specific cases are in acceptance/production-cases.md.

## Authoritative daily editorial behavior

See handoff/product-scope-v3.md. Rolling last24hourdeveloper-focused research, all findings reachable, priority descending with source-backed explanations and explicit independent approval/publication. Earlier undated illustrative topics or broader recency filters must not appear as fresh daily news.

