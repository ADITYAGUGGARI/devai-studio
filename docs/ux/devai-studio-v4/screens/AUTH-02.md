# AUTH-02 — Check your email

Purpose: Confirm a time-limited email code. Web route `/sign-in/verify`; iOS destination `DevAI/AUTH-02`. Parent: AUTH-01; preserve invoker on reusable editor/preview.

## Composition

Desktop: Same 440px form, expiry and masked destination above inputs. At1440px use232px sidebar,32px page gutter and24px gaps; dedicated editors suppress ordinary shell content navigation but retain Done, entity title and Activity status.

iOS: One numeric autofill input, native Back to sign in. Physical viewport390×844 with top safe area47 and bottom34; content scrolls between navigation and fixed actions. Body17pt,44pt targets. Native child editor hides tab bar and uses Done/Back; root destinations keep five tabs. Long form continuation is scrolling content, not a tall fictional phone.

Content and focus order: Six digit code → Verify → Resend in 30s → Change email. Read boundary: Proposed /v1 resource matching exact operation index; public auth requires no workspace read. Only the contracts below mutate. All IDs are stable, not row indices.

## Controls — authoritative revision 3

| ID/control | Preconditions/trigger | Action and success | Operation/request | Exact next destination | Failure and recovery |
|---|---|---|---|---|---|
|AUTH-02-I01 code|Editable form, or public authentication field; Input/change; editor autosave800ms or explicit Save|Update local form buffer; 6numeric digits; one input; oneTimeCode. Commit only on form Save or editor autosave.|None on input; owning form Save contract 6numeric digits; one input; oneTimeCode|/sign-in/verify|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|AUTH-02-I02 verify-code|Unexpired challenge and six digits; Click/Enter/Space or native tap; drag has Move before/after alternative|Set session, load workspaces; ONB-01 if none, otherwise safe returnTo|POST /v1/auth/email/verify {challengeId,code}|ONB-01 if no workspace; otherwise validated returnTo or HOME-01|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|AUTH-02-I03 resend|server resendAfter elapsed; Click/Enter/Space or native tap; drag has Move before/after alternative|Replace challenge; clear code; reset resend timer|POST /v1/auth/email/challenges {email,replaceChallengeId}|Remain on /sign-in/verify with acknowledged revision/state; no implicit publication or navigation|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|AUTH-02-I04 change-email|Read permission for requested entity; public routes exempt; Click/Enter/Space or native tap; drag has Move before/after alternative|Open AUTH-01 for selected authorized entity; preserve originating route, tab stack and scroll.|None: local UI/navigation; destination resource read only No payload|AUTH-01|Read failure retains last loaded content labeled stale with Retry; denied/missing target opens SYS-02; offline navigation uses cached authorized content. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|

## State and persistence contract

Applicable states: initial, loading, populated, failure, permission_denied, session_expired, offline, reconnecting. Loading reserves actual layout using skeletons for lists, inline spinner only for submitted control; empty list explains scope and offers Clear filters or relevant create action. Do not show an empty screen while loading. Offline exposes cached timestamp, queues only protected text edits, and disables generation, approval and publication with explanation. Session expiry keeps protected local buffer and returns here after authentication. Permission loss immediately removes mutation actions while preserving permitted read view.

Editors save800ms after idle, ordered per entity with expectedRevision. Saved requires ACK; failure retains buffer and Save now.409 displays field-level base/mine/server comparison; accepting server never silently deletes mine. Back/Done with unacknowledged buffer offers Save, Discard local changes, Stay; selecting Save must succeed before leaving. Navigation never cancels durable jobs. Read-only screens have no autosave, draft, or paid action merely because they share components.

Dialogs follow interactions/dialogs.md; per-control triggers and responses are in interactions.json. Native focus enters screen title; web route title receives focus except returning to original invoker. Preview revision is labeled and retained; latest revision refresh cannot silently swap an approved preview.

## Visuals and tests

Desktop `visuals/desktop/AUTH-02-default.svg`; iOS `visuals/ios/AUTH-02-default.svg`. Per-control tests: AUTH-02-AT01, AUTH-02-AT02, AUTH-02-AT03, AUTH-02-AT04. Critical state-specific cases are in acceptance/production-cases.md.

