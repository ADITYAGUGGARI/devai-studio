# SET-09 — Security & sessions

Purpose: Manage active devices and account protection. Web route `/settings/security`; iOS destination `DevAI/SET-09`. Parent: SET-01; preserve invoker on reusable editor/preview.

## Composition

Desktop: Device/session table with last seen and recent-auth destructive action. At1440px use232px sidebar,32px page gutter and24px gaps; dedicated editors suppress ordinary shell content navigation but retain Done, entity title and Activity status.

iOS: Session rows and confirmation sheets, current device tagged. Physical viewport390×844 with top safe area47 and bottom34; content scrolls between navigation and fixed actions. Body17pt,44pt targets. Native child editor hides tab bar and uses Done/Back; root destinations keep five tabs. Long form continuation is scrolling content, not a tall fictional phone.

Content and focus order: Current session → Other sessions → Revoke → Apple link → Sign out. Read boundary: Proposed /v1 resource matching exact operation index; public auth requires no workspace read. Only the contracts below mutate. All IDs are stable, not row indices.

## Controls — authoritative revision 3

| ID/control | Preconditions/trigger | Action and success | Operation/request | Exact next destination | Failure and recovery |
|---|---|---|---|---|---|
|SET-09-I01 session-revoke|Authenticated workspace and permitted role; Click/Enter/Space or native tap; drag has Move before/after alternative|Revoke selected device refresh token; keep current session unless selected|DELETE /v1/sessions/{sessionId} {recentAuthProof}|Remain on /settings/security with acknowledged revision/state; no implicit publication or navigation|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|SET-09-I02 link-apple|Authenticated workspace and permitted role; Click/Enter/Space or native tap; drag has Move before/after alternative|Link authenticated identity; no workspace merge without explicit verification|POST /v1/me/apple {identityToken,nonce,recentAuthProof}|Remain on /settings/security with acknowledged revision/state; no implicit publication or navigation|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|SET-09-I03 sign-out|Local buffers synchronized or explicitly exported/discarded; Click/Enter/Space or native tap; drag has Move before/after alternative|Clear session/cache and push binding; AUTH-01|POST /v1/auth/logout {allDevices:boolean}|AUTH-01 after protected buffer decision and server session revocation|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|SET-09-I04 sign-out-all|Local buffers synchronized or explicitly exported/discarded; Click/Enter/Space or native tap; drag has Move before/after alternative|Clear session/cache and push binding; AUTH-01|POST /v1/auth/logout {allDevices:boolean}|AUTH-01 after session revocation|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|

## State and persistence contract

Applicable states: initial, loading, populated, failure, permission_denied, session_expired, offline, reconnecting, validation_error, unsaved, autosaving, saved, save_failed, conflict. Loading reserves actual layout using skeletons for lists, inline spinner only for submitted control; empty list explains scope and offers Clear filters or relevant create action. Do not show an empty screen while loading. Offline exposes cached timestamp, queues only protected text edits, and disables generation, approval and publication with explanation. Session expiry keeps protected local buffer and returns here after authentication. Permission loss immediately removes mutation actions while preserving permitted read view.

Editors save800ms after idle, ordered per entity with expectedRevision. Saved requires ACK; failure retains buffer and Save now.409 displays field-level base/mine/server comparison; accepting server never silently deletes mine. Back/Done with unacknowledged buffer offers Save, Discard local changes, Stay; selecting Save must succeed before leaving. Navigation never cancels durable jobs. Read-only screens have no autosave, draft, or paid action merely because they share components.

Dialogs follow interactions/dialogs.md; per-control triggers and responses are in interactions.json. Native focus enters screen title; web route title receives focus except returning to original invoker. Preview revision is labeled and retained; latest revision refresh cannot silently swap an approved preview.

## Visuals and tests

Desktop `visuals/desktop/SET-09-default.svg`; iOS `visuals/ios/SET-09-default.svg`. Per-control tests: SET-09-AT01, SET-09-AT02, SET-09-AT03, SET-09-AT04. Critical state-specific cases are in acceptance/production-cases.md.

