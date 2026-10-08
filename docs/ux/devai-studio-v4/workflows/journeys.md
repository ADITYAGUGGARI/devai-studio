# End-to-end journey specifications

Every journey uses the shared persistence, interaction, role, state and accessibility rules. Backend references are cataloged separately; proposed contracts are explicitly labeled.

## A — Discover AI news
Goal: Discover AI news. Entry points: Home/Discover/Add topic. Start: DISC-01.
Preconditions: authenticated authorized workspace, latest entity status; AUTH is public. Generation needs human-reviewed usable evidence and configured format capabilities. Publishing needs explicit permission and a current approval snapshot.

Actions, decisions and backend: Read GET /topics; search and filter dated saved evidence; open topic; inspect source; save or Create. Refresh enqueues research rather than erasing results.

Failure and alternate paths: No results → clear filters; duplicate source → open canonical topic/draft; inaccessible source → saved excerpt + access warning; >14-day news flagged older; undated not labeled new. Paginate 24 stable rows; stale cursor reset keeps filters.

Progress: stage-specific durable units; local control pending indicators; no fictitious elapsed-time percent. Success: acknowledged server status, announced politely, affected caches refreshed. Cancellation: navigation alone leaves durable operations running; explicit cooperative cancel where eligible. Retry: preserved units and same action key after status check, following job policy. Back: invoking route and filters retained; pending local edits governed by D-UNSAVED. Persistence: server revisions and immutable assets; device buffer only until acknowledgement. Notifications: outcome/change-required event, in-app always, opt-in push per preferences. Desktop: sidebar + dedicated workspace/inspector; iOS: five independent tab stacks, native pushes/sheets and focused forms.

Exit conditions: Exit at saved topic or durable setup; no implicit topic selection from opening a card.
Acceptance: A-AT01 through A-AT05 in acceptance/criteria.md, plus control-level tests in acceptance/control-tests.csv.

## B — Daily research
Goal: Daily research. Entry points: Home run / Settings schedule / Discover refresh. Start: SET-03.
Preconditions: authenticated authorized workspace, latest entity status; AUTH is public. Generation needs human-reviewed usable evidence and configured format capabilities. Publishing needs explicit permission and a current approval snapshot.

Actions, decisions and backend: Save schedule separately from publishing; worker health and next run shown; run creates date/timezone unique job; Activity shows source units; available topics inserted transactionally and daily history preserved.

Failure and alternate paths: Queued/running/retry_wait/completed/completed_with_warnings/failed are existing; proposed stalled/cancelling/cancelled extend contract. Partial result opens usable topics and grouped source errors. Empty no usable evidence fails, all duplicates is successful no-new result. Stalled requires server heartbeat, never inferred just from browser disconnection.

Progress: stage-specific durable units; local control pending indicators; no fictitious elapsed-time percent. Success: acknowledged server status, announced politely, affected caches refreshed. Cancellation: navigation alone leaves durable operations running; explicit cooperative cancel where eligible. Retry: preserved units and same action key after status check, following job policy. Back: invoking route and filters retained; pending local edits governed by D-UNSAVED. Persistence: server revisions and immutable assets; device buffer only until acknowledgement. Notifications: outcome/change-required event, in-app always, opt-in push per preferences. Desktop: sidebar + dedicated workspace/inspector; iOS: five independent tab stacks, native pushes/sheets and focused forms.

Exit conditions: Exit completed/partial/cancelled/failed with reviewable history; never claim schedule active without server heartbeat.
Acceptance: B-AT01 through B-AT05 in acceptance/criteria.md, plus control-level tests in acceptance/control-tests.csv.

## C — Verify a topic
Goal: Verify a topic. Entry points: Topic sources / failed grounding report / Review. Start: SOURCE-01.
Preconditions: authenticated authorized workspace, latest entity status; AUTH is public. Generation needs human-reviewed usable evidence and configured format capabilities. Publishing needs explicit permission and a current approval snapshot.

Actions, decisions and backend: Inspect publisher, URL, published/retrieved dates and exact excerpt; review factual claims against contiguous quotations; classify AI interpretation separately; correct/remove unsupported copy; choose source-backed editorial angle.

Failure and alternate paths: A primary publisher label is identity, not truth; a matching quotation supports attribution, not external proof. Unsupported numeric/code claims block submission; stale evidence warns and requires recheck. Updating manual excerpt resets verification. Source failure preserves prior snapshot; manual evidence possible without bypassing restrictions.

Progress: stage-specific durable units; local control pending indicators; no fictitious elapsed-time percent. Success: acknowledged server status, announced politely, affected caches refreshed. Cancellation: navigation alone leaves durable operations running; explicit cooperative cancel where eligible. Retry: preserved units and same action key after status check, following job policy. Back: invoking route and filters retained; pending local edits governed by D-UNSAVED. Persistence: server revisions and immutable assets; device buffer only until acknowledgement. Notifications: outcome/change-required event, in-app always, opt-in push per preferences. Desktop: sidebar + dedicated workspace/inspector; iOS: five independent tab stacks, native pushes/sheets and focused forms.

Exit conditions: Exit with human-reviewed evidence and no unresolved blocking factual claims; recorded actor/version/timestamp.
Acceptance: C-AT01 through C-AT05 in acceptance/criteria.md, plus control-level tests in acceptance/control-tests.csv.

## D — Create content
Goal: Create content. Entry points: Topic Create / Library Create. Start: CREATE-01.
Preconditions: authenticated authorized workspace, latest entity status; AUTH is public. Generation needs human-reviewed usable evidence and configured format capabilities. Publishing needs explicit permission and a current approval snapshot.

Actions, decisions and backend: Choose Carousel/Reel/Both based on available capabilities; configure audience/tone/language/brief, 6–8 slides and/or 30–40s; review provider status/estimated work and authorize generation; save setup and obtain durable content/job IDs.

Failure and alternate paths: Provider unavailable disables affected format with reason and settings link; no fallback to ungrounded copy. Both creates two output jobs with independent partial results. Estimates shown only with real provider data; unknown cost says Estimate unavailable. Network unknown start resolves by idempotency key before retry.

Progress: stage-specific durable units; local control pending indicators; no fictitious elapsed-time percent. Success: acknowledged server status, announced politely, affected caches refreshed. Cancellation: navigation alone leaves durable operations running; explicit cooperative cancel where eligible. Retry: preserved units and same action key after status check, following job policy. Back: invoking route and filters retained; pending local edits governed by D-UNSAVED. Persistence: server revisions and immutable assets; device buffer only until acknowledgement. Notifications: outcome/change-required event, in-app always, opt-in push per preferences. Desktop: sidebar + dedicated workspace/inspector; iOS: five independent tab stacks, native pushes/sheets and focused forms.

Exit conditions: Exit when server acknowledges jobs or saves setup; closing configuration never starts generation.
Acceptance: D-AT01 through D-AT05 in acceptance/criteria.md, plus control-level tests in acceptance/control-tests.csv.

## E — Generate carousel
Goal: Generate carousel. Entry points: Start generation / Retry job / Artwork action. Start: GEN-01.
Preconditions: authenticated authorized workspace, latest entity status; AUTH is public. Generation needs human-reviewed usable evidence and configured format capabilities. Publishing needs explicit permission and a current approval snapshot.

Actions, decisions and backend: Ground outline/copy; generate each full composition; dimension/transcription/legibility/duplicate validation; persist immutable assets per slide; show actual completed counts; ready output opens editor.

Failure and alternate paths: Grounding rejection creates diagnostics, no approvable fabricated draft. Failed slide retains diagnostic asset, marked not ready; reuse passing units. Existing paid two-pass repair remains transparent. Cancellation safe checkpoint, retains committed units. Copy-only draft explicitly lacks images and cannot be review ready.

Progress: stage-specific durable units; local control pending indicators; no fictitious elapsed-time percent. Success: acknowledged server status, announced politely, affected caches refreshed. Cancellation: navigation alone leaves durable operations running; explicit cooperative cancel where eligible. Retry: preserved units and same action key after status check, following job policy. Back: invoking route and filters retained; pending local edits governed by D-UNSAVED. Persistence: server revisions and immutable assets; device buffer only until acknowledgement. Notifications: outcome/change-required event, in-app always, opt-in push per preferences. Desktop: sidebar + dedicated workspace/inspector; iOS: five independent tab stacks, native pushes/sheets and focused forms.

Exit conditions: Exit only current 6–8 1080×1350 PNG assets validated and source-linked; human review still required.
Acceptance: E-AT01 through E-AT05 in acceptance/criteria.md, plus control-level tests in acceptance/control-tests.csv.

## F — Edit carousel
Goal: Edit carousel. Entry points: Library output / generation result / revision feedback. Start: CAR-01.
Preconditions: authenticated authorized workspace, latest entity status; AUTH is public. Generation needs human-reviewed usable evidence and configured format capabilities. Publishing needs explicit permission and a current approval snapshot.

Actions, decisions and backend: Select stable slide; edit copy/brief; local buffer autosaves revision-checked; artwork becomes stale; regenerate selected composition with old version preserved; reorder via drag or Move menu; add/remove within 6–8 submission bounds; inspect history; preview and submit.

Failure and alternate paths: No direct baked-image text overlays or rigid layout controls. Save failure retains typed text. Switching slide retains pending buffer. Conflict offers field-level comparison, not last-write-wins. Restoring old asset whose hash mismatches copy remains stale. Approval invalidates before changed revision becomes publishable.

Progress: stage-specific durable units; local control pending indicators; no fictitious elapsed-time percent. Success: acknowledged server status, announced politely, affected caches refreshed. Cancellation: navigation alone leaves durable operations running; explicit cooperative cancel where eligible. Retry: preserved units and same action key after status check, following job policy. Back: invoking route and filters retained; pending local edits governed by D-UNSAVED. Persistence: server revisions and immutable assets; device buffer only until acknowledgement. Notifications: outcome/change-required event, in-app always, opt-in push per preferences. Desktop: sidebar + dedicated workspace/inspector; iOS: five independent tab stacks, native pushes/sheets and focused forms.

Exit conditions: Exit server-saved current version, all assets validated and caption/evidence complete; submit moves only this format to review.
Acceptance: F-AT01 through F-AT05 in acceptance/criteria.md, plus control-level tests in acceptance/control-tests.csv.

## G — Generate Reel
Goal: Generate Reel. Entry points: Creation Reel/Both / scene retry. Start: GEN-01.
Preconditions: authenticated authorized workspace, latest entity status; AUTH is public. Generation needs human-reviewed usable evidence and configured format capabilities. Publishing needs explicit permission and a current approval snapshot.

Actions, decisions and backend: Persist source-grounded script → storyboard → scene visual assets → audio → timed subtitles → rendering → MP4 rendered → MP4 validated → ready for review. Label every milestone independently.

Failure and alternate paths: Script/storyboard never a completed video. Scene failure retries affected scene; audio failure offers retry/change voice or deliberate silent version with subtitles; rendering failure retains scenes/audio, retry assembly. Validate decoding, duration, dimensions, audio, subtitle bounds and hashes.

Progress: stage-specific durable units; local control pending indicators; no fictitious elapsed-time percent. Success: acknowledged server status, announced politely, affected caches refreshed. Cancellation: navigation alone leaves durable operations running; explicit cooperative cancel where eligible. Retry: preserved units and same action key after status check, following job policy. Back: invoking route and filters retained; pending local edits governed by D-UNSAVED. Persistence: server revisions and immutable assets; device buffer only until acknowledgement. Notifications: outcome/change-required event, in-app always, opt-in push per preferences. Desktop: sidebar + dedicated workspace/inspector; iOS: five independent tab stacks, native pushes/sheets and focused forms.

Exit conditions: Exit validated 30–40-second 1080×1920 vertical MP4; approval still pending.
Acceptance: G-AT01 through G-AT05 in acceptance/criteria.md, plus control-level tests in acceptance/control-tests.csv.

## H — Edit Reel
Goal: Edit Reel. Entry points: Library output / review changes. Start: REEL-01.
Preconditions: authenticated authorized workspace, latest entity status; AUTH is public. Generation needs human-reviewed usable evidence and configured format capabilities. Publishing needs explicit permission and a current approval snapshot.

Actions, decisions and backend: Desktop player above scene/narration/music tracks; select inspector; edit script/scenes/audio/cues; seek real MP4; adjust duration; preview audio; render immutable timeline revision; inspect new validated MP4; submit. iOS opens full-screen editor with Preview/Scenes/Script/Audio/Subtitles tools; scene cards and focused numeric timing sheets.

Failure and alternate paths: Old render stays playable labeled “Rendered v7 · edits v8 need render.” Never substitute thumbnails as MP4. Timeline reorder retimes scenes/cues; audio exceeding scene duration blocks render or explicit retime. Failed render preserves edit revision. Leaving editor does not cancel server render.

Progress: stage-specific durable units; local control pending indicators; no fictitious elapsed-time percent. Success: acknowledged server status, announced politely, affected caches refreshed. Cancellation: navigation alone leaves durable operations running; explicit cooperative cancel where eligible. Retry: preserved units and same action key after status check, following job policy. Back: invoking route and filters retained; pending local edits governed by D-UNSAVED. Persistence: server revisions and immutable assets; device buffer only until acknowledgement. Notifications: outcome/change-required event, in-app always, opt-in push per preferences. Desktop: sidebar + dedicated workspace/inspector; iOS: five independent tab stacks, native pushes/sheets and focused forms.

Exit conditions: Exit latest validated MP4 matching current timeline; no stale-render review.
Acceptance: H-AT01 through H-AT05 in acceptance/criteria.md, plus control-level tests in acceptance/control-tests.csv.

## I — Review and approve
Goal: Review and approve. Entry points: Review queue / Home review count / editor submit. Start: REVIEW-02.
Preconditions: authenticated authorized workspace, latest entity status; AUTH is public. Generation needs human-reviewed usable evidence and configured format capabilities. Publishing needs explicit permission and a current approval snapshot.

Actions, decisions and backend: Open one format; inspect every slide or watch entire Reel with seek permitted; review sources/claims/caption/technical code; record version-bound checklist; approve confirmation or request specific changes. Self-review allowed for personal owner; collaborators need reviewer role.

Failure and alternate paths: Carousel and Reel independent. Stale assets, unsupported claims, incomplete/legacy compositions block. Change request records feedback, returns format to changes_requested (legacy rejected), never automatically spends generation credits. Concurrent edits yield 409 and checklist resets. Published snapshot immutable.

Progress: stage-specific durable units; local control pending indicators; no fictitious elapsed-time percent. Success: acknowledged server status, announced politely, affected caches refreshed. Cancellation: navigation alone leaves durable operations running; explicit cooperative cancel where eligible. Retry: preserved units and same action key after status check, following job policy. Back: invoking route and filters retained; pending local edits governed by D-UNSAVED. Persistence: server revisions and immutable assets; device buffer only until acknowledgement. Notifications: outcome/change-required event, in-app always, opt-in push per preferences. Desktop: sidebar + dedicated workspace/inspector; iOS: five independent tab stacks, native pushes/sheets and focused forms.

Exit conditions: Exit approved hash-bound snapshot or saved revision request; no publication follows approval.
Acceptance: I-AT01 through I-AT05 in acceptance/criteria.md, plus control-level tests in acceptance/control-tests.csv.

## J — Publish or schedule
Goal: Publish or schedule. Entry points: Approved output / Calendar / Content detail. Start: PUB-01.
Preconditions: authenticated authorized workspace, latest entity status; AUTH is public. Generation needs human-reviewed usable evidence and configured format capabilities. Publishing needs explicit permission and a current approval snapshot.

Actions, decisions and backend: Select account and one approved format version; server preflight; review exact caption/media; resolve local time + zone + UTC; explicit final Publish or Schedule creates reservation; monitor durable attempt; show external link only confirmed. Both selected means two separate posts, clearly disclose and confirm each.

Failure and alternate paths: Past/<5-minute scheduled times rejected; DST gap rejected and overlap choice required. Expired token/permission/rate limit/media rejection blocks or fails with reason. Once final publish may have been accepted, outcome unknown locks reservation; no retry. Read account/Meta then reconcile published ID+note or confirmed not published (returns draft for reapproval).

Progress: stage-specific durable units; local control pending indicators; no fictitious elapsed-time percent. Success: acknowledged server status, announced politely, affected caches refreshed. Cancellation: navigation alone leaves durable operations running; explicit cooperative cancel where eligible. Retry: preserved units and same action key after status check, following job policy. Back: invoking route and filters retained; pending local edits governed by D-UNSAVED. Persistence: server revisions and immutable assets; device buffer only until acknowledgement. Notifications: outcome/change-required event, in-app always, opt-in push per preferences. Desktop: sidebar + dedicated workspace/inspector; iOS: five independent tab stacks, native pushes/sheets and focused forms.

Exit conditions: Exit confirmed published, durable schedule, confirmed failure, or locked unknown state requiring reconciliation. Never publish from generation/approval/notification tap.
Acceptance: J-AT01 through J-AT05 in acceptance/criteria.md, plus control-level tests in acceptance/control-tests.csv.

## K — Content library
Goal: Content library. Entry points: Content tab / Home / notification. Start: LIB-01.
Preconditions: authenticated authorized workspace, latest entity status; AUTH is public. Generation needs human-reviewed usable evidence and configured format capabilities. Publishing needs explicit permission and a current approval snapshot.

Actions, decisions and backend: Search/filter/sort/page all statuses and formats; open exact output; duplicate as new draft; archive; export asset package; soft-delete to 30-day Trash; restore. Published output offers duplicate to edit and View on Instagram.

Failure and alternate paths: Active generation warns cancellation needed before delete; publication reservation/unknown blocks archive/delete/purge. Export failed keeps content intact. Draft export watermark/metadata identifies unapproved; full-resolution assets not altered. Legacy current-image export compatibility retained; no implied approval.

Progress: stage-specific durable units; local control pending indicators; no fictitious elapsed-time percent. Success: acknowledged server status, announced politely, affected caches refreshed. Cancellation: navigation alone leaves durable operations running; explicit cooperative cancel where eligible. Retry: preserved units and same action key after status check, following job policy. Back: invoking route and filters retained; pending local edits governed by D-UNSAVED. Persistence: server revisions and immutable assets; device buffer only until acknowledgement. Notifications: outcome/change-required event, in-app always, opt-in push per preferences. Desktop: sidebar + dedicated workspace/inspector; iOS: five independent tab stacks, native pushes/sheets and focused forms.

Exit conditions: Exit selected content or completed reversible management/export; external Instagram post unaffected by local deletion.
Acceptance: K-AT01 through K-AT05 in acceptance/criteria.md, plus control-level tests in acceptance/control-tests.csv.

## L — Activity and notifications
Goal: Activity and notifications. Entry points: Activity tab / header bell / push. Start: ACT-01.
Preconditions: authenticated authorized workspace, latest entity status; AUTH is public. Generation needs human-reviewed usable evidence and configured format capabilities. Publishing needs explicit permission and a current approval snapshot.

Actions, decisions and backend: Read durable jobs with units/attempts/stage; inspect diagnostics; retry safe eligible operations; open affected entity; mark notification read; adjust push preferences. Server emits deduplicated outcome events.

Failure and alternate paths: Push denial never blocks app; silent background push unreliable and not required. Foreground announces key phase only. Job list timeout preserves cached rows and last-updated timestamp; job unknown reconciles on return. Publish retry absent.

Progress: stage-specific durable units; local control pending indicators; no fictitious elapsed-time percent. Success: acknowledged server status, announced politely, affected caches refreshed. Cancellation: navigation alone leaves durable operations running; explicit cooperative cancel where eligible. Retry: preserved units and same action key after status check, following job policy. Back: invoking route and filters retained; pending local edits governed by D-UNSAVED. Persistence: server revisions and immutable assets; device buffer only until acknowledgement. Notifications: outcome/change-required event, in-app always, opt-in push per preferences. Desktop: sidebar + dedicated workspace/inspector; iOS: five independent tab stacks, native pushes/sheets and focused forms.

Exit conditions: Exit recovered job or acknowledged event with retained history.
Acceptance: L-AT01 through L-AT05 in acceptance/criteria.md, plus control-level tests in acceptance/control-tests.csv.

## M — Analytics
Goal: Analytics. Entry points: Analytics web nav / Home shortcut / Settings iOS. Start: ANA-01.
Preconditions: authenticated authorized workspace, latest entity status; AUTH is public. Generation needs human-reviewed usable evidence and configured format capabilities. Publishing needs explicit permission and a current approval snapshot.

Actions, decisions and backend: Choose account/date/format; read cached supported metrics with fetched/coverage metadata; inspect post; compare 2–4 compatible posts by same range or age; export filtered CSV/PDF.

Failure and alternate paths: Unavailable or permission-restricted metrics show — plus reason, never zero. No demographic/AI insight claims without real supported data. Disconnect retains historic snapshots with stale marker. Partial coverage does not calculate misleading growth; missing denominator means engagement rate unavailable. Export job retry safe.

Progress: stage-specific durable units; local control pending indicators; no fictitious elapsed-time percent. Success: acknowledged server status, announced politely, affected caches refreshed. Cancellation: navigation alone leaves durable operations running; explicit cooperative cancel where eligible. Retry: preserved units and same action key after status check, following job policy. Back: invoking route and filters retained; pending local edits governed by D-UNSAVED. Persistence: server revisions and immutable assets; device buffer only until acknowledgement. Notifications: outcome/change-required event, in-app always, opt-in push per preferences. Desktop: sidebar + dedicated workspace/inspector; iOS: five independent tab stacks, native pushes/sheets and focused forms.

Exit conditions: Exit factual metric inspection or completed export; source/account/date range preserved.
Acceptance: M-AT01 through M-AT05 in acceptance/criteria.md, plus control-level tests in acceptance/control-tests.csv.

## N — Settings and integrations
Goal: Settings and integrations. Entry points: Settings tab / contextual correction link. Start: SET-01.
Preconditions: authenticated authorized workspace, latest entity status; AUTH is public. Generation needs human-reviewed usable evidence and configured format capabilities. Publishing needs explicit permission and a current approval snapshot.

Actions, decisions and backend: Manage profile/workspace/research/provider/account/push/security independently; validate section; test connections; save atomically; sensitive actions require recent auth; credentials server-side. OAuth opens system browser on iOS with state-bound return.

Failure and alternate paths: Bad key retains old working connection; deny/cancel OAuth returns unchanged account list; disconnect pauses future schedules, accepted publications reconcile; cannot remove last owner. Permission loss read-only with preserved unsynced draft. Security changes revoke selected sessions with exact consequences.

Progress: stage-specific durable units; local control pending indicators; no fictitious elapsed-time percent. Success: acknowledged server status, announced politely, affected caches refreshed. Cancellation: navigation alone leaves durable operations running; explicit cooperative cancel where eligible. Retry: preserved units and same action key after status check, following job policy. Back: invoking route and filters retained; pending local edits governed by D-UNSAVED. Persistence: server revisions and immutable assets; device buffer only until acknowledgement. Notifications: outcome/change-required event, in-app always, opt-in push per preferences. Desktop: sidebar + dedicated workspace/inspector; iOS: five independent tab stacks, native pushes/sheets and focused forms.

Exit conditions: Exit acknowledged preference revision or tested integration state; never show Connected from merely storing a key.
Acceptance: N-AT01 through N-AT05 in acceptance/criteria.md, plus control-level tests in acceptance/control-tests.csv.

## O — Cross-device continuity
Goal: Cross-device continuity. Entry points: Foreground/reload/reconnect/deep link. Start: VER-01.
Preconditions: authenticated authorized workspace, latest entity status; AUTH is public. Generation needs human-reviewed usable evidence and configured format capabilities. Publishing needs explicit permission and a current approval snapshot.

Actions, decisions and backend: Start on desktop; durable job continues server-side; iOS foreground obtains authoritative entity/job/revision; resume editing/review; idempotency keys deduplicate same action; merge disjoint field edits with fresh precondition.

Failure and alternate paths: Offline local draft stored encrypted/protected per device; no offline approval/publishing/provider test. Same-field conflict shows Mine/Server side-by-side and explicit Keep mine/Keep server/manual merge; no silent overwrite. Session change hides previous account cache. Asset write for stale revision discarded.

Progress: stage-specific durable units; local control pending indicators; no fictitious elapsed-time percent. Success: acknowledged server status, announced politely, affected caches refreshed. Cancellation: navigation alone leaves durable operations running; explicit cooperative cancel where eligible. Retry: preserved units and same action key after status check, following job policy. Back: invoking route and filters retained; pending local edits governed by D-UNSAVED. Persistence: server revisions and immutable assets; device buffer only until acknowledgement. Notifications: outcome/change-required event, in-app always, opt-in push per preferences. Desktop: sidebar + dedicated workspace/inspector; iOS: five independent tab stacks, native pushes/sheets and focused forms.

Exit conditions: Exit synchronized revision or explicit unresolved conflict/local export; jobs do not depend on a foreground app.
Acceptance: O-AT01 through O-AT05 in acceptance/criteria.md, plus control-level tests in acceptance/control-tests.csv.

## AUTH — Authentication and onboarding
Goal: Authentication and onboarding. Entry points: App launch / session recovery. Start: AUTH-01.
Preconditions: authenticated authorized workspace, latest entity status; AUTH is public. Generation needs human-reviewed usable evidence and configured format capabilities. Publishing needs explicit permission and a current approval snapshot.

Actions, decisions and backend: Email challenge or native Apple sign-in; generic response; verify code; establish secure session; choose personal workspace and optional preferences; integrations can be skipped; protected return link resumes after auth.

Failure and alternate paths: Invalid/expired code inline; retry limit cooldown; resend rate limited; OAuth/Apple cancel stays sign-in; network retains email/code until safe expiry; auth renewal fails to SYS-01 with unsaved buffer preserved. No public production API key login.

Progress: stage-specific durable units; local control pending indicators; no fictitious elapsed-time percent. Success: acknowledged server status, announced politely, affected caches refreshed. Cancellation: navigation alone leaves durable operations running; explicit cooperative cancel where eligible. Retry: preserved units and same action key after status check, following job policy. Back: invoking route and filters retained; pending local edits governed by D-UNSAVED. Persistence: server revisions and immutable assets; device buffer only until acknowledgement. Notifications: outcome/change-required event, in-app always, opt-in push per preferences. Desktop: sidebar + dedicated workspace/inspector; iOS: five independent tab stacks, native pushes/sheets and focused forms.

Exit conditions: Exit authenticated scoped session and onboarded workspace, or accessible recovery.
Acceptance: AUTH-AT01 through AUTH-AT05 in acceptance/criteria.md, plus control-level tests in acceptance/control-tests.csv.


## Authoritative creation-path update

D: Topic→CREATE-01format→CREATE-03default summary→Generate. Preferences is optional CREATE-02→CREATE-03. E/G: evidence/outline→AI fresh concept planning→full slide/scene generation→dimensions/transcript/media checks→visual similarity checks→carousel editor or full MP4 render/validation. F/H: copy correction and automatic Regenerate/Different look, no manual layout input. PC-AI01..09 and handoff/ai-creative-autopilot.md define failure/retry/budget behavior and supersede earlier creative-direction fields.
