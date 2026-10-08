# Component contracts

Props are semantic cross-platform contracts; web and React Native implementations differ. Server state belongs in a query/cache layer; Jotai is appropriate for local editor selection, local buffers and overlay state. Never store provider credentials or authoritative approval in client atoms. Python/PostgreSQL contracts own permissions, versions, jobs and publication authorization.

| Component | Props | Variants and states | Interaction/accessibility |
|---|---|---|---|
| Button | label, variant, disabledReason, pending, onPress | primary/secondary/ghost/destructive; default/hover/pressed/focus/pending/disabled | Single action, idempotency protection; accessible button label and state |
| Field | id,label,value,onChange,error,hint,required,limit | text/textarea/email/url/secure/numeric; focused/invalid/readOnly | Visible label + describedby; counter announces on threshold, not every character |
| Select | label,options,value,disabledOptions,onChange | native iOS picker; web combobox | Keyboard typeahead/arrow/Escape; return focus; no fake dropdown |
| Toggle | label,checked,onChange,consequence | off/on/pending/disabled | Switch semantics; if paid/scheduling consequence, separate Save/confirm |
| StatusBadge | status,label,reason | neutral/success/warning/error/running | Text+icon; static not clickable unless explicit job link |
| TopicRow | topic,source,freshness,onOpen,onSave | queued/saved/archived/used/unverified | Card title link and independent save button; no nested buttons |
| OutputRow | output,revision,approval,publication | carousel/reel + independent state | Primary open; menu only eligible actions; actual thumbnail |
| SourcePanel | snapshot,claimRefs,verification,onOpen | official identity/human reviewed/unsupported/access failure | Verbatim excerpt, dates and quote anchors; copy/open explicit |
| ClaimRow | claim,quote,snapshotId,match,classification | supported/unsupported/interpretation/pending | Explain support scope; unresolved blocks relevant approval |
| MediaViewer | asset,kind,revision,validation,controls | image/video/storyboard/missing/stale | Actual media only; image alt/copy transcript; native player accessibility |
| SlideStrip | orderedIds,selectedId,onSelect,onMove | selected/stale/generating/failed | Roving keyboard selection; Move up/down alternatives; native accessible reorder actions |
| SceneList | scenes,selectedId,onEdit,onMove | ready/missing/failed/stale | iOS cards with durations; ordinal and accessibility move actions |
| Timeline | tracks,playhead,selection,onSeek,onTrim | scene/voice/music/cues; stale render | Numeric timing alternatives; keyboard seek; no infinite small handles on iOS |
| SaveStatus | revision,state,lastSaved,retry | unsaved/autosaving/saved/failed/conflict | Polite concise announcement; persistent error action |
| JobProgress | job,units,heartbeat,actions | all defined job statuses | Actual units and stages; no estimated percentage without denominator |
| DialogSheet | title,body,actions,onDismiss,dirty | confirmation/form/picker/conflict | Web trap; native detents; close/back policy and focus restore |
| ToastBanner | eventId,severity,message,action,dismiss | toast/inline/banner/inbox | Important errors persistent; live announcement deduplicated |
| ListToolbar | query,filters,sort,view,onApply | default/filtered/fetching/empty | URL state; native filter sheet; pagination cursor |
| MetricPanel | value,unit,definition,coverage,fetchedAt | available/unavailable/partial/stale | Zero only known zero; chart accessible table; no speculative insight |
| AccountConnection | identity,scopes,expiry,lastTest,actions | connecting/connected/expired/denied/disconnected | Never plaintext secret; state-based recovery |
| Navigation | destinations,selected,badges,stacks | expanded/collapsed/native/mobile-web | aria-current; labeled icons; persistent native tabs |
| VersionCompare | base,mine,server,fields,onResolve | diff/selection/merge/commit/conflict | No silent overwrite; preserved local buffer; large sheet/full route |
| EmptyPanel | title,reason,primaryAction | no-data/no-results/disconnected | One relevant action; no fake counts |
| Pagination | cursor,count,onNext,error | loading/loaded/failure/end | Focus stays on Load more; new count announced |
