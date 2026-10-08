# Shared state treatment contract

Applicability is recorded for every screen in screens/screens.json. Loading includes nonshimmer skeletons; a spinner is reserved for short localized action waits. Completed is a durable job result; success is an acknowledged UI action. Stalled/cancellation are proposed capabilities, not current API status values.

| State | Treatment | Recovery |
|---|---|---|
| initial | Layout frame and heading immediately | Fetch authorized data; no initial fake counts |
| loading | Skeleton only for first read; aria-busy region | Retry inline if failed; controls not tied to fetch remain available |
| empty | Plain icon/title/reason + one contextual primary action | Discover clear filters or Research; library Create; analytics Connect; no fake data |
| populated | True content, provenance and revision | Eligible actions only; status never solely color |
| validation_error | Inline field error and summary on submit | Focus first invalid field; preserve all input |
| failure | Inline panel with reason, action and safe diagnostic code | Retain cached data and user input; no global block for local failure |
| permission_denied | Read-only/access banner; sensitive contents hidden when access revoked | Owner contact/switch workspace; no indefinite retry |
| session_expired | SYS-01 sheet/banner with Sign in | Preserve private draft buffer; resume safe intended route after auth |
| offline | Persistent “Offline · showing saved data” banner | Reads cached; buffer edits; disable approval/publish/paid actions with reason |
| reconnecting | “Reconnecting…” banner; keep content stable | Fetch versions before flushing; unknown mutations checked by key |
| success | Local acknowledged state; brief polite notification | Navigate only when useful, never auto-publish |
| partial_success | Usable results plus warning counts and failed units | Open successful assets; retry only unresolved safe units |
| queued | “Waiting for worker” and queue timestamp | Leave page safely; no invented ETA |
| running | Actual stage + completed units, separate format cards | Background work; controls for same output locked; other output usable |
| stalled | Server-detected “No worker update” with last heartbeat | Wait/recover job; publishing requires outcome check; proposed health contract |
| cancelling | “Stopping after the current step…” | Disable repeated cancellation; retain completed work |
| cancelled | “Stopped · saved completed assets” | Open draft/restart remaining units if supported |
| retryable_failure | Actionable unit error + Retry + next automatic attempt time | No manual retry before correction for key/billing/source validation |
| permanent_failure | Configuration/unsupported status with correction link | No useless retry button; preserve assets and diagnostics |
| unsaved | Editor status “Unsaved changes” | Local durable buffer; prevent silent loss on navigation |
| autosaving | Small “Saving…” live status | No full-screen spinner; sequence writes per entity |
| saved | “Saved · [time]” only after response | Server revision is displayed on details/history |
| save_failed | Persistent editor error “Changes are saved on this device only” | Retry after authoritative read; export local text available |
| conflict | D-CONFLICT comparison sheet | Manual resolve; immutable server version; never last-write-wins |
| background | Compact stage summary with View progress | User may leave app; no claim iOS can render indefinitely in background |
| completed | Exact result: research counts, validated PNGs or validated MP4 | Ready for review only after validation; no automatic approval |
