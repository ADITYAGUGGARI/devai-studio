# SET-11 — Data & privacy

Purpose: Export data and request account removal. Web route `/settings/data`; iOS destination `DevAI/SET-11`. Parent: SET-01; preserve invoker on reusable editor/preview.

## Composition

Desktop: Privacy explanation, export job and deletion cooling-off date. At1440px use232px sidebar,32px page gutter and24px gaps; dedicated editors suppress ordinary shell content navigation but retain Done, entity title and Activity status.

iOS: Native settings privacy section, recent-auth deletion confirmation. Physical viewport390×844 with top safe area47 and bottom34; content scrolls between navigation and fixed actions. Body17pt,44pt targets. Native child editor hides tab bar and uses Done/Back; root destinations keep five tabs. Long form continuation is scrolling content, not a tall fictional phone.

Content and focus order: Export my data → Delete account → Privacy → Help. Read boundary: Proposed /v1 resource matching exact operation index; public auth requires no workspace read. Only the contracts below mutate. All IDs are stable, not row indices.

## Controls — authoritative revision 3

| ID/control | Preconditions/trigger | Action and success | Operation/request | Exact next destination | Failure and recovery |
|---|---|---|---|---|---|
|SET-11-I01 export-data|Authenticated workspace and permitted role; Click/Enter/Space or native tap; drag has Move before/after alternative|Durable export job; expiring24h download; secrets omitted|POST /v1/data/exports {recentAuthProof}|Remain on /settings/data with acknowledged revision/state; no implicit publication or navigation|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|SET-11-I02 delete-account|Owner resolved reservations; typed studio name; warns external posts remain; Click/Enter/Space or native tap; drag has Move before/after alternative|Deletion scheduled7days; cancel available until execution|POST /v1/account/deletion {recentAuthProof,confirmedRetention:true}|Remain on /settings/data with acknowledged revision/state; no implicit publication or navigation|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|SET-11-I03 privacy|Read permission for requested entity; public routes exempt; Click/Enter/Space or native tap; drag has Move before/after alternative|Open SET-11 for selected authorized entity; preserve originating route, tab stack and scroll.|None: local UI/navigation; destination resource read only No payload|SET-11|Read failure retains last loaded content labeled stale with Retry; denied/missing target opens SYS-02; offline navigation uses cached authorized content. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|SET-11-I04 help|Read permission for requested entity; public routes exempt; Click/Enter/Space or native tap; drag has Move before/after alternative|Open HELP-01 for selected authorized entity; preserve originating route, tab stack and scroll.|None: local UI/navigation; destination resource read only No payload|HELP-01|Read failure retains last loaded content labeled stale with Retry; denied/missing target opens SYS-02; offline navigation uses cached authorized content. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|
|SET-11-I05 cancel-deletion|Current saved entity; server capability and permission; online; Input/change; editor autosave800ms or explicit Save|Cancel pending account deletion before effective date after recent authentication.|DELETE /v1/account/deletion Expected revision, input hashes and explicit confirmation; contract-addenda.md|/settings/data|422: attach field errors and retain input;403: read-only permission banner;401: SYS-01 with safe return;409: show current state and retain draft; network: retain buffer and fetch authoritative state before retry. Retry safe reads freely; mutation retries reuse same key after status fetch; never retry uncertain external publication. Cancel form keeps acknowledged revision; cancel job only via server checkpoint.|

## State and persistence contract

Applicable states: initial, loading, populated, failure, permission_denied, session_expired, offline, reconnecting, validation_error, unsaved, autosaving, saved, save_failed, conflict. Loading reserves actual layout using skeletons for lists, inline spinner only for submitted control; empty list explains scope and offers Clear filters or relevant create action. Do not show an empty screen while loading. Offline exposes cached timestamp, queues only protected text edits, and disables generation, approval and publication with explanation. Session expiry keeps protected local buffer and returns here after authentication. Permission loss immediately removes mutation actions while preserving permitted read view.

Editors save800ms after idle, ordered per entity with expectedRevision. Saved requires ACK; failure retains buffer and Save now.409 displays field-level base/mine/server comparison; accepting server never silently deletes mine. Back/Done with unacknowledged buffer offers Save, Discard local changes, Stay; selecting Save must succeed before leaving. Navigation never cancels durable jobs. Read-only screens have no autosave, draft, or paid action merely because they share components.

Dialogs follow interactions/dialogs.md; per-control triggers and responses are in interactions.json. Native focus enters screen title; web route title receives focus except returning to original invoker. Preview revision is labeled and retained; latest revision refresh cannot silently swap an approved preview.

## Visuals and tests

Desktop `visuals/desktop/SET-11-default.svg`; iOS `visuals/ios/SET-11-default.svg`. Per-control tests: SET-11-AT01, SET-11-AT02, SET-11-AT03, SET-11-AT04. Critical state-specific cases are in acceptance/production-cases.md.

## Additional required action

SET-11-I05 `cancel-deletion`: Cancel pending account deletion before effective date after recent authentication. Operation `DELETE /v1/account/deletion`; request and recovery: contracts/contract-addenda.md. Acceptance SET-11-AT05.

