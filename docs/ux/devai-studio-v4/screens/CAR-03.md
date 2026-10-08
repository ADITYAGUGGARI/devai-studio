# CAR-03 — Regenerate artwork

Purpose: Create a new composition while preserving old assets. Web route `/content/:contentId/carousel/regenerate/:slideId`; iOS destination `DevAI/CAR-03`. Parent: CAR-01; preserve invoker on reusable editor/preview.

## Composition

Desktop: 560px dialog with preserved current image and paid action footer. At1440px use232px sidebar,32px page gutter and24px gaps; dedicated editors suppress ordinary shell content navigation but retain Done, entity title and Activity status.

iOS: Medium/large sheet with read-only AI plan, Generate and Cancel. Physical viewport390×844 with top safe area47 and bottom34; content scrolls between navigation and fixed actions. Body17pt,44pt targets. Native child editor hides tab bar and uses Done/Back; root destinations keep five tabs. Long form continuation is scrolling content, not a tall fictional phone.

Content and focus order: Regeneration brief → Current image → New generation authorization. Read boundary: GET /posts/{id}. Only the contracts below mutate. All IDs are stable, not row indices.

## Controls — authoritative revision 3

| ID/control | Preconditions/trigger | Action and success | Operation/request | Exact next destination | Failure and recovery |
|---|---|---|---|---|---|
|CAR-03-I02 regenerate-confirm|Saved current copy and automatic concept; provider ready; confirmed cost action; Click/Enter/Space or native tap; drag has Move before/after alternative|202 scoped job; retain previous asset until new current validated asset AI chooses a different background/composition using recent creative history; no manual layout prompt.|POST /v1/outputs/{outputId}/slides/{slideId}/generate {expectedRevision,confirmed:true}|Remain on /content/:contentId/carousel/regenerate/:slideId with acknowledged revision/state; no implicit publication or navigation|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|CAR-03-I03 cancel|Read permission for requested entity; public routes exempt; Click/Enter/Space or native tap; drag has Move before/after alternative|Dismiss uncommitted form/sheet and restore invoker focus; does not cancel active durable job.|None: local UI/navigation; destination resource read only No payload|/content/:contentId/carousel/regenerate/:slideId|Read failure retains last loaded content labeled stale with Retry; denied/missing target opens SYS-02; offline navigation uses cached authorized content. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|CAR-03-AI3 inspect-creative-plan|Authorized current output; mutation saved revision and explicit additional budget; Input/change; editor autosave800ms or explicit Save|Open read-only AI plan or nearest recent output comparison; no layout input|GET /v1/outputs/{outputId}/creative-plan ai-creative-autopilot.md|/content/:contentId/carousel/regenerate/:slideId|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|

## State and persistence contract

Applicable states: initial, loading, populated, failure, permission_denied, session_expired, offline, reconnecting, validation_error, unsaved, autosaving, saved, save_failed, conflict. Loading reserves actual layout using skeletons for lists, inline spinner only for submitted control; empty list explains scope and offers Clear filters or relevant create action. Do not show an empty screen while loading. Offline exposes cached timestamp, queues only protected text edits, and disables generation, approval and publication with explanation. Session expiry keeps protected local buffer and returns here after authentication. Permission loss immediately removes mutation actions while preserving permitted read view.

Editors save800ms after idle, ordered per entity with expectedRevision. Saved requires ACK; failure retains buffer and Save now.409 displays field-level base/mine/server comparison; accepting server never silently deletes mine. Back/Done with unacknowledged buffer offers Save, Discard local changes, Stay; selecting Save must succeed before leaving. Navigation never cancels durable jobs. Read-only screens have no autosave, draft, or paid action merely because they share components.

Dialogs follow interactions/dialogs.md; per-control triggers and responses are in interactions.json. Native focus enters screen title; web route title receives focus except returning to original invoker. Preview revision is labeled and retained; latest revision refresh cannot silently swap an approved preview.

## Visuals and tests

Desktop `visuals/desktop/CAR-03-default.svg`; iOS `visuals/ios/CAR-03-default.svg`. Per-control tests: CAR-03-AT01, CAR-03-AT02, CAR-03-AT03. Critical state-specific cases are in acceptance/production-cases.md.

## Latest user requirement — AI autonomy and varied content

Authoritative: handoff/ai-creative-autopilot.md. No required visual brief/layout/background input. AI creates whole compositions and Reel assets automatically and checks recent/scheduled visual history. Regenerate chooses a fresh AI direction; prior assets retained. App UI palette does not constrain Instagram artwork. Full Reel must be validated MP4.

CAR-03-AI3 inspect-creative-plan: Open read-only AI plan or nearest recent output comparison; no layout input; GET /v1/outputs/{outputId}/creative-plan; test CAR-03-AI3-AT.


