# NOT-01 — Notifications

Purpose: Follow meaningful workflow events. Web route `/notifications`; iOS destination `DevAI/NOT-01`. Parent: Invoking tab; preserve invoker on reusable editor/preview.

## Composition

Desktop: List with event type, relative and exact timestamp, entity destination. At1440px use232px sidebar,32px page gutter and24px gaps; dedicated editors suppress ordinary shell content navigation but retain Done, entity title and Activity status.

iOS: Home stack notification inbox, unread selected trait. Physical viewport390×844 with top safe area47 and bottom34; content scrolls between navigation and fixed actions. Body17pt,44pt targets. Native child editor hides tab bar and uses Done/Back; root destinations keep five tabs. Long form continuation is scrolling content, not a tall fictional phone.

Content and focus order: Unread → All → Mark all read → Notification rows → Preferences. Read boundary: Proposed /v1 resource matching exact operation index; public auth requires no workspace read. Only the contracts below mutate. All IDs are stable, not row indices.

## Controls — authoritative revision 3

| ID/control | Preconditions/trigger | Action and success | Operation/request | Exact next destination | Failure and recovery |
|---|---|---|---|---|---|
|NOT-01-I01 notification-open|Read permission for requested entity; public routes exempt; Click/Enter/Space or native tap; drag has Move before/after alternative|Mark selected event read through notification read contract, navigate authorized entity; deleted/denied entity shows SYS-02 without sensitive title.|None: local UI/navigation; destination resource read only No payload|/notifications|Read failure retains last loaded content labeled stale with Retry; denied/missing target opens SYS-02; offline navigation uses cached authorized content. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|NOT-01-I02 mark-read|Authenticated workspace and permitted role; Click/Enter/Space or native tap; drag has Move before/after alternative|Persist read without affecting underlying job|PATCH /v1/notifications/{notificationId}/read {read:true}|Remain on /notifications with acknowledged revision/state; no implicit publication or navigation|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|NOT-01-I03 mark-all-read|Authenticated workspace and permitted role; Click/Enter/Space or native tap; drag has Move before/after alternative|Mark only events at or before captured inbox head read|POST /v1/notifications/read-all {throughEventId}|Remain on /notifications with acknowledged revision/state; no implicit publication or navigation|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|NOT-01-I04 notification-filter|Editable form, or public authentication field; Input/change; editor autosave800ms or explicit Save|Update local form buffer; Unread/All with stable cursor. Commit only on form Save or editor autosave.|None on input; owning form Save contract Unread/All with stable cursor|/notifications|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|NOT-01-I05 notification-settings|Read permission for requested entity; public routes exempt; Click/Enter/Space or native tap; drag has Move before/after alternative|Open SET-08 for selected authorized entity; preserve originating route, tab stack and scroll.|None: local UI/navigation; destination resource read only No payload|SET-08|Read failure retains last loaded content labeled stale with Retry; denied/missing target opens SYS-02; offline navigation uses cached authorized content. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|

## State and persistence contract

Applicable states: initial, loading, populated, failure, permission_denied, session_expired, offline, reconnecting, empty, skeleton. Loading reserves actual layout using skeletons for lists, inline spinner only for submitted control; empty list explains scope and offers Clear filters or relevant create action. Do not show an empty screen while loading. Offline exposes cached timestamp, queues only protected text edits, and disables generation, approval and publication with explanation. Session expiry keeps protected local buffer and returns here after authentication. Permission loss immediately removes mutation actions while preserving permitted read view.

Editors save800ms after idle, ordered per entity with expectedRevision. Saved requires ACK; failure retains buffer and Save now.409 displays field-level base/mine/server comparison; accepting server never silently deletes mine. Back/Done with unacknowledged buffer offers Save, Discard local changes, Stay; selecting Save must succeed before leaving. Navigation never cancels durable jobs. Read-only screens have no autosave, draft, or paid action merely because they share components.

Dialogs follow interactions/dialogs.md; per-control triggers and responses are in interactions.json. Native focus enters screen title; web route title receives focus except returning to original invoker. Preview revision is labeled and retained; latest revision refresh cannot silently swap an approved preview.

## Visuals and tests

Desktop `visuals/desktop/NOT-01-default.svg`; iOS `visuals/ios/NOT-01-default.svg`. Per-control tests: NOT-01-AT01, NOT-01-AT02, NOT-01-AT03, NOT-01-AT04, NOT-01-AT05. Critical state-specific cases are in acceptance/production-cases.md.

