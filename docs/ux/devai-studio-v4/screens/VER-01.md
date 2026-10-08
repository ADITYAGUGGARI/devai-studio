# VER-01 — Version history

Purpose: Compare and restore a saved version safely. Web route `/content/:contentId/versions`; iOS destination `DevAI/VER-01`. Parent: Invoking editor; preserve invoker on reusable editor/preview.

## Composition

Desktop: 300px version list, two canvas panes with changed fields below. At1440px use232px sidebar,32px page gutter and24px gaps; dedicated editors suppress ordinary shell content navigation but retain Done, entity title and Activity status.

iOS: Version rows push read-only preview, compare segmented Old/Current. Physical viewport390×844 with top safe area47 and bottom34; content scrolls between navigation and fixed actions. Body17pt,44pt targets. Native child editor hides tab bar and uses Done/Back; root destinations keep five tabs. Long form continuation is scrolling content, not a tall fictional phone.

Content and focus order: Version history → Actor → Timestamp → Compare → Restore as draft. Read boundary: Proposed /v1 resource matching exact operation index; public auth requires no workspace read. Only the contracts below mutate. All IDs are stable, not row indices.

## Controls — authoritative revision 3

| ID/control | Preconditions/trigger | Action and success | Operation/request | Exact next destination | Failure and recovery |
|---|---|---|---|---|---|
|VER-01-I01 version-select|Read permission for requested entity; public routes exempt; Click/Enter/Space or native tap; drag has Move before/after alternative|Select stable entity ID; highlight and announce position; show current revision detail; flush pending entity edits before switching; failed save offers Stay or keep buffer.|None: local UI/navigation; destination resource read only No payload|/content/:contentId/versions|Read failure retains last loaded content labeled stale with Retry; denied/missing target opens SYS-02; offline navigation uses cached authorized content. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|VER-01-I02 compare-version|Read permission for requested entity; public routes exempt; Click/Enter/Space or native tap; drag has Move before/after alternative|Show historical and current snapshot with text/asset hash differences; read-only; no restore until explicit Restore as draft.|None: local UI/navigation; destination resource read only No payload|/content/:contentId/versions|Read failure retains last loaded content labeled stale with Retry; denied/missing target opens SYS-02; offline navigation uses cached authorized content. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|VER-01-I03 restore-version|Authenticated workspace and permitted role; Click/Enter/Space or native tap; drag has Move before/after alternative|Create new draft head; never copy approval; editor opens restored draft|POST /v1/outputs/{outputId}/restore {expectedRevision,historicalRevision}|Remain on /content/:contentId/versions with acknowledged revision/state; no implicit publication or navigation|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|VER-01-I04 back|Read permission for requested entity; public routes exempt; Click/Enter/Space or native tap; drag has Move before/after alternative|Return invoking route/stack and scroll; dirty unacknowledged edits open Save/Discard/Stay decision; durable jobs continue.|None: local UI/navigation; destination resource read only No payload|/content/:contentId/versions|Read failure retains last loaded content labeled stale with Retry; denied/missing target opens SYS-02; offline navigation uses cached authorized content. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|

## State and persistence contract

Applicable states: initial, loading, populated, failure, permission_denied, session_expired, offline, reconnecting. Loading reserves actual layout using skeletons for lists, inline spinner only for submitted control; empty list explains scope and offers Clear filters or relevant create action. Do not show an empty screen while loading. Offline exposes cached timestamp, queues only protected text edits, and disables generation, approval and publication with explanation. Session expiry keeps protected local buffer and returns here after authentication. Permission loss immediately removes mutation actions while preserving permitted read view.

Editors save800ms after idle, ordered per entity with expectedRevision. Saved requires ACK; failure retains buffer and Save now.409 displays field-level base/mine/server comparison; accepting server never silently deletes mine. Back/Done with unacknowledged buffer offers Save, Discard local changes, Stay; selecting Save must succeed before leaving. Navigation never cancels durable jobs. Read-only screens have no autosave, draft, or paid action merely because they share components.

Dialogs follow interactions/dialogs.md; per-control triggers and responses are in interactions.json. Native focus enters screen title; web route title receives focus except returning to original invoker. Preview revision is labeled and retained; latest revision refresh cannot silently swap an approved preview.

## Visuals and tests

Desktop `visuals/desktop/VER-01-default.svg`; iOS `visuals/ios/VER-01-default.svg`. Per-control tests: VER-01-AT01, VER-01-AT02, VER-01-AT03, VER-01-AT04. Critical state-specific cases are in acceptance/production-cases.md.

