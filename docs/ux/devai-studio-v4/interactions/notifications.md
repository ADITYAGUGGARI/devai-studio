# Notifications and exact message patterns

| ID | Surface | Trigger | Copy | Action |
|---|---|---|---|---|
| N-SAVED | Toast/status | Acknowledged save | Changes saved. | polite; 4sec; no required action |
| N-SAVE-FAILED | Persistent inline | Save request failed | Changes are saved on this device only. Retry when connected. | Retry / export local text |
| N-RESEARCH | In-app + opt-in push | Research outcome | Research finished: {new} new topics, {duplicate} already known, {failed} source warnings. | Open job; push hides private title by default |
| N-READY | In-app + opt-in push | Validated output ready | Your {format} is ready for review. | Review exact version; never auto-approve |
| N-CHANGES | In-app + opt-in push | Reviewer feedback saved | Changes requested for {format}. | Open feedback; no automatic generation |
| N-PUBLISHED | In-app + opt-in push | Confirmed external media ID | Published to {handle}. | View on Instagram or library |
| N-UNKNOWN | Persistent banner + in-app/push | Publishing may have succeeded | Publishing outcome is unknown. Check Instagram before trying again. | Reconcile; no Retry |
| N-SCHEDULED | Toast + calendar row | Schedule acknowledged | Scheduled for {date}, {time} {zone}. | View schedule; actual server resolved time |
| N-TOKEN | Banner + in-app/push | Credentials invalid/expired | Reconnect {handle} to continue publishing. | Reconnect; affected schedules blocked |
| N-OFFLINE | Persistent banner | Transport offline | Offline · showing saved data. | Recheck state on connection; no queued publish |
| N-CONFLICT | Persistent inline + sheet | Revision mismatch | This content changed on another device. | Compare changes |
| N-VALIDATION | Inline summary | Submit invalid | Fix the highlighted fields to continue. | Focus first invalid |
| N-NO-NEW | Inline job result | Research all duplicates | No new topics. {count} sources are already in your queue or library. | Open queue; not empty-news fabrication |
| N-RENDER-FAILED | Inline + in-app/push | Render failed | Rendering failed. Your scenes and audio are saved. | Inspect reason; retry safe render |
| N-PERMISSION | Banner | Access revoked | You no longer have permission to change this workspace. | Switch workspace; export only authorized local work |

Notifications are deduplicated by event ID + entity revision; persist in inbox even if toast dismissed. Toasts never hold the only copy of an error, approval, unknown outcome or important recovery action. Foreground device receives in-app outcome; push opt-in per category and quiet hours, delivered by server; content remains available if delivery fails. No secrets, source excerpts or drafts on lock screen by default. Push opens authenticated deep link and fetches live status before presenting actions. Notification badge counts unread actionable events, not every progress tick. Mark all read requires acknowledged mutation and supports undo locally then server within 5s.
