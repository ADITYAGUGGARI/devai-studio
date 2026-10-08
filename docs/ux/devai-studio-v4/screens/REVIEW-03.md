# REVIEW-03 — Request changes

Purpose: Record actionable feedback without triggering paid generation. Web route `/review/:contentId/:format/changes`; iOS destination `DevAI/REVIEW-03`. Parent: REVIEW-02; preserve invoker on reusable editor/preview.

## Composition

Desktop: 560px dialog with per-slide/scene selection and note. At1440px use232px sidebar,32px page gutter and24px gaps; dedicated editors suppress ordinary shell content navigation but retain Done, entity title and Activity status.

iOS: Large sheet with target picker and note, keyboard-safe Send request. Physical viewport390×844 with top safe area47 and bottom34; content scrolls between navigation and fixed actions. Body17pt,44pt targets. Native child editor hides tab bar and uses Done/Back; root destinations keep five tabs. Long form continuation is scrolling content, not a tall fictional phone.

Content and focus order: Revision targets → Required note → Send request → Cancel. Read boundary: GET /posts/{id}. Only the contracts below mutate. All IDs are stable, not row indices.

## Controls — authoritative revision 3

| ID/control | Preconditions/trigger | Action and success | Operation/request | Exact next destination | Failure and recovery |
|---|---|---|---|---|---|
|REVIEW-03-I01 revision-target|Editable form, or public authentication field; Input/change; editor autosave800ms or explicit Save|Update local form buffer; one or more output units or Caption/Sources/Overall. Commit only on form Save or editor autosave.|None on input; owning form Save contract one or more output units or Caption/Sources/Overall|/review/:contentId/:format/changes|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|REVIEW-03-I02 revision-note|Editable form, or public authentication field; Input/change; editor autosave800ms or explicit Save|Update local form buffer; 10–2000characters. Commit only on form Save or editor autosave.|None on input; owning form Save contract 10–2000characters|/review/:contentId/:format/changes|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|REVIEW-03-I03 submit-changes|Reviewer/Owner; target selected; note10–2000; Click/Enter/Space or native tap; drag has Move before/after alternative|Output changes_requested; editor receives inbox event; no auto generation|POST /v1/outputs/{outputId}/changes {expectedRevision,targets,note}|REVIEW-01 after acknowledged feedback|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|REVIEW-03-I04 cancel|Read permission for requested entity; public routes exempt; Click/Enter/Space or native tap; drag has Move before/after alternative|Dismiss uncommitted form/sheet and restore invoker focus; does not cancel active durable job.|None: local UI/navigation; destination resource read only No payload|/review/:contentId/:format/changes|Read failure retains last loaded content labeled stale with Retry; denied/missing target opens SYS-02; offline navigation uses cached authorized content. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|

## State and persistence contract

Applicable states: initial, loading, populated, failure, permission_denied, session_expired, offline, reconnecting, validation_error, unsaved, autosaving, saved, save_failed, conflict. Loading reserves actual layout using skeletons for lists, inline spinner only for submitted control; empty list explains scope and offers Clear filters or relevant create action. Do not show an empty screen while loading. Offline exposes cached timestamp, queues only protected text edits, and disables generation, approval and publication with explanation. Session expiry keeps protected local buffer and returns here after authentication. Permission loss immediately removes mutation actions while preserving permitted read view.

Editors save800ms after idle, ordered per entity with expectedRevision. Saved requires ACK; failure retains buffer and Save now.409 displays field-level base/mine/server comparison; accepting server never silently deletes mine. Back/Done with unacknowledged buffer offers Save, Discard local changes, Stay; selecting Save must succeed before leaving. Navigation never cancels durable jobs. Read-only screens have no autosave, draft, or paid action merely because they share components.

Dialogs follow interactions/dialogs.md; per-control triggers and responses are in interactions.json. Native focus enters screen title; web route title receives focus except returning to original invoker. Preview revision is labeled and retained; latest revision refresh cannot silently swap an approved preview.

## Visuals and tests

Desktop `visuals/desktop/REVIEW-03-default.svg`; iOS `visuals/ios/REVIEW-03-default.svg`. Per-control tests: REVIEW-03-AT01, REVIEW-03-AT02, REVIEW-03-AT03, REVIEW-03-AT04. Critical state-specific cases are in acceptance/production-cases.md.

