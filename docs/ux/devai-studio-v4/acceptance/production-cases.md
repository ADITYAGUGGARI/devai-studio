# Concrete acceptance cases — release gates

Use fixtures.md. These are behavior specifications to be implemented against fake providers and sandbox accounts; they have not been executed against the application. Test web keyboard, native touch/VoiceOver, and reconnect paths. A successful visual export is not a passing application test.

| ID | Given | When | Then |
|---|---|---|---|
| PC-A01 | Discover has24topics and nextCursor K1 | Search 'durable', then change to 'sources' before first response | Debounce300ms, abort first read, only second query appears; URL stores q; no mutation or research spend |
| PC-A02 | Filter Tools yields no items | Clear filters | Query and cursor reset; skeleton only on uncached read; nonempty cached list remains until response |
| PC-A03 | T1 canonical URL exists | Import same normalized HTTPS URL with tracking parameters |409duplicate links T1; excerpt buffer retained; no second topic or draft |
| PC-A04 | Source captured yesterday but publication is20days old | Open T1 | Show separate published/captured dates; older-news label; no 'breaking' inference |
| PC-B01 | Daily research off, timezone Chicago, time08:00 | Save daily enabled | Show server-confirmed next occurrence; do not run now; no schedule success if worker unavailable |
| PC-B02 | J1 already running | Run research from two devices | Same active key returns same jobID; one background run; both devices show Activity link |
| PC-B03 | Research10sources,7succeeded,3failed | Job completes | Completed with warnings;7usable results preserved; source failures grouped; retry only failed units |
| PC-B04 | Browser loses connection while worker heartbeat remains current | Reconnect after60sec | No stalled inference during disconnect; fetch server status; display current units and completed topics |
| PC-B05 | J1 canCancel true | Stop job then close phone | Cancelling persists server-side until checkpoint; retained topics available; no silent rollback |
| PC-C01 | Claim quote differs by one word from saved E1 | Run grounding | Unsupported exact-quote match flagged; fact cannot pass review; source publisher alone never yields verified fact |
| PC-C02 | Unsupported factual statement appears in S2 | Exclude claim | Affected copy must remove unsupported assertion; asset stale; approve disabled until new validated artwork |
| PC-C03 | Reviewer corrects evidence snapshot E1 shared by O1 and O2 | Save new E2 | Both dependent approval snapshots invalidated; scheduled reservations depending on superseded evidence blocked pending reapproval; unrelated evidence unaffected |
| PC-D01 | Both selected, image provider ready, renderer missing | Continue generation review | Carousel eligible; Reel block names missing renderer; no hidden downgrade; choose Carousel explicitly or connect renderer |
| PC-D02 | Saved setup revision3 | Double-tap Generate Both | Same intent key creates one C1 and separate O1/O2jobs; buttons pending; no duplicate charge authorization |
| PC-D03 | Generate accepted202 | Cancel wizard or close browser | Generation continues; library lists both outputs; navigation is not cancellation |
| PC-E01 | J2 partial S1..S6ready,S7failed,S8queued | Retry S7 | Only S7 regenerated; successful asset hashes unchanged; slide-level progress truthful |
| PC-E02 | S7new image returned width1024,height1024 | Validate asset | Not review-ready; normalize only if compliant composition preserved, otherwise failed dimensions; current old valid asset stays in history |
| PC-E03 | Valid new S7 asset arrives for revision12 but output nowrevision13 | Worker commits | Asset associated with original input snapshot; cannot silently become current for edited copy; UI labels stale |
| PC-F01 | O1revision12current AP1approved | Edit S2headline | Local Unsaved immediately, after800ms PATCH expected12; on ACKrevision13 draft, AP1invalid, S2art stale, other image hashes retained |
| PC-F02 | Buffer B1 edits S2, serverrevision13 edits S3 | Save B1 |409conflict shows base/mine/server; merge applies S2mine+S3server; CAS expected13; no overwrite |
| PC-F03 | Same S2field edited on both devices | Choose Mine then Save | Explicit chosen text commits as newrevision; second409 keeps merge and current server values; cannot force overwrite silently |
| PC-F04 | Save returns500 | Select S3 or Back | S2buffer remains; Save now/Stay offered; Saved never shown; navigation only after explicit keep-buffer policy or discard |
| PC-F05 | Eight slides contain baked ordinal artwork | Move S2afterS5 with keyboard or VoiceOver | Atomic orderedIDs, selected S2stable; renumbered assets stale; no overlay text shortcut; approval invalidated |
| PC-F06 | Three paid regenerations completed | Undo last copy edit | Inverse copy revision created; no provider call, no history deletion; selected old artwork current only if exact hash inputs match |
| PC-G01 | Reel script and storyboard ready, no encoded media | Open GEN-02 | 'Storyboard ready' and assets stage shown; no MP4download, no Ready for review badge |
| PC-G02 | Visuals ready, voice generation failed | Retry voice | Visual hashes unchanged; no silent fallback to no audio; explicit No voice requires user selection and render |
| PC-G03 | MP4 rendered35sec but decoder validation failed | Render finishes | 'MP4 rendered · validation failed'; review disabled; retry validation or render with diagnostics; file not labeled completed Reel |
| PC-G04 | R7valid, new renderR8fails | Open Reel | R7playable labeled retained rendition; editable timeline stale; cannot approveR7as current edited revision |
| PC-H01 | Native REEL-01 at390×844 | Edit scene3 | Push REEL-04; numeric duration field and visual brief; no tiny desktop timeline; Back returns scene3scroll position |
| PC-H02 | Playback12sec | Scrub to20sec, mute and enter landscape | Preview seek/mute only; no timeline revision; exiting fullscreen retains20sec and mute state |
| PC-H03 | Cue2start5sec,end9sec | Set start10sec or overlapCue3 | Inline validation; preserve inputs; no invalid timeline PATCH; focus first error |
| PC-H04 | Total duration35sec | Increase scene7by8sec | Local total43sec warning; save draft permitted, Render and Submit blocked until30–40sec; no automatic scene shortening |
| PC-H05 | Uploaded music rights checkbox off | Select file and Save | Media uploaded/decoded privately but unavailable for render until license captured; no imaginary licensed music library |
| PC-I01 | O1ready, O2rendering | Approve Carousel | AP1covers O1only; O2unchanged; Carousel publish eligible; Reel approval disabled |
| PC-I02 | Reviewer has not viewedS8 | Check Assets reviewed | Control explains Slide8unviewed; Approve disabled; reading checklist alone not enough |
| PC-I03 | Reviewer opens revision12, author savesrevision13 | Confirm approval |409current version changed; checks reset as affected, preview explicitly opens13; no approval of unseen revision |
| PC-I04 | Request note empty | Send changes | Inline note minimum10characters; no job generation or state transition until valid submit |
| PC-J01 | AP1current, IG1selected | Tap Publish now in final named-account dialog | One durable authorization/attempt created; frozen revision12caption/media; PUB-02status; no other content published |
| PC-J02 | Final external publish times out, result unknown | Retry from web/phone | No retry control; J4needs reconciliation, reservation locked; user opens PUB-03; no duplicate post |
| PC-J03 | Time2026-11-01 01:30 Chicago ambiguous | Schedule | Require First occurrence -05:00 or Second -06:00; store UTC06:30Z or07:30Zrespectively; confirmation shows chosen offset |
| PC-J04 | Time2027-03-14 02:30 Chicago nonexistent | Schedule | Reject gap inline, offer03:00; user must select valid time; never normalize silently |
| PC-J05 | P1scheduled snapshotrevision12 | Edit working outputrevision13 | Calendar still shows Scheduled v12, detail shows Editing v13; media/caption replacement needs reapproval plus explicit Update schedule authorization |
| PC-J06 | IG1credentials expire before slot | Scheduler claims preflight | Blocked, inbox/push; no blind retry or catch-up; reconnect leaves paused; explicit Publish now/Reschedule required |
| PC-J07 | Cancel and scheduler claim race | Confirm Cancel schedule | Atomic one winner; if final publish accepted show Too late to cancel and current status; no false Cancelled |
| PC-J08 | Owner confirms published with no externalID | Save outcome | Inline externalIDrequired; lock retained; valid externalID+note attaches one receipt; Not published requires evidence then returns draft/reapproval |
| PC-J09 | Rate limit before final publish call | Receive retryAfter | Scheduled blocked/retryable safe preparation with server retry time; final uncertain call never retried automatically; reason distinguishes phase |
| PC-K01 | C1activeunknown publication | Delete or permanent delete | Disabled with outcome resolution reason; no asset loss; Duplicate creates new independent draft only |
| PC-K02 | Trash C1day29 | Restore | Content restored; versions retained; no automatic generation or publication; retention timer removed |
| PC-K03 | Selected exportrevision12, latestrevision13 | Download | Download exact selected12assets+caption+evidence manifest; never mix revisions |
| PC-L01 | Job fails twice with same eventID | Push and inbox delivered | Single durable inbox item; push deduplicated; opening authorized entity marks read without retrying job |
| PC-L02 | Push denied | Enable push again | Show Open iOS Settings; no repeated OS request; in-app inbox still receives events |
| PC-M01 | Reach unavailable, likes known0 | Open analytics | Reach displays Unavailable with reason; likes0displayed0; chart/table agree, no fabricated engagement rate |
| PC-M02 | Two compared posts have3and7days of metrics | Compare first7days | Partial coverage marked for younger post; no false full7day comparison; export includes coverage and null reasons |
| PC-N01 | Existing provider connection works | Test bad replacement key | Failed test inline; existing connection retained; key never logged or reread; Save new connection disabled |
| PC-N02 | Workspace soleOwner | Remove/demote self | Server rejects LAST_OWNER; role remains; no client-only enforcement |
| PC-N03 | Research off and auto draft off | Save profile timezone | New future research occurrence uses new zone only if enabled; authorized publications keep stored UTC andoriginal zone |
| PC-O01 | Desktop job accepted then browser closes | Open iOS | Fetch job by server ID; show current stage without enqueue; remaining assets and exact working revision available |
| PC-O02 | Offline textbufferB1, session expires | Sign in as another user | Buffer inaccessible to new user/workspace; no cross-account merge; original user may restore/export after reauth |
| PC-O03 | Background phone app suspended during upload | Resume | Server completed uploads/parts reconciled; explicit remaining chunk retry with uploadID; no entire paid scene repeat |
| PC-X01 | Web viewport320 and zoom200percent | Navigate every destination | Drawer provides all routes, no hidden sidebar-only links; forms one column, no horizontal page scroll; editor canvas fits with explicit zoom |
| PC-X02 | VoiceOver and largest Dynamic Type | Approve/reconcile/editor conflict | Content scrolls and actions remain reachable, labels read once, selected state/ordinal announced, modal title focus and invoker restoration |
| PC-X03 | Reduced Motion on | Navigate generation and editor | No shimmer, looping animation or auto-scroll; textual progress updates; player does not autoplay |
| PC-URL01 | URL-only idea accepted202, extraction stillrunning | Leave Discover then reopen idea on iOS | Fetch existing idea/job; no duplicate extraction; show captured excerpt only after completion; Add topic requires manual review |
| PC-URL02 | Article access denied | Open extraction failure | Original URL retained; Paste reviewed excerpt action switches mode; no generated filler or unsupported factual topic inserted |
| PC-AI01 | TopicT1reviewed, Carousel selected, no visual instructions | Generate | AI plans fresh concept and produces8full1080×1350images; user never required to select layout/background or supply art prompt |
| PC-AI02 | Last10published/scheduled posts share beige geometric backgrounds | Generate nextpost | Plan chooses meaningfully different background/composition/medium; comparison reports count and nearest match; app UI palette not forced into artwork |
| PC-AI03 | New asset hash exactly matches last published image | Validate | Exact duplicate blocked, automatic alternate concept within budget; approval impossible for repeated hash |
| PC-AI04 | Near duplicate remains after2alternate concepts | Validation completes | Budget exhausted warning with preserved draft; Try a different look requires explicit additional authorization; no infinite charges |
| PC-AI05 | Both selected on two devices | Submit identical setup intent | One content intent, separate format jobs and one coordinated concept reservation; no duplicate spend or identical untracked concepts |
| PC-AI06 | Same topic appears in an intentional series but visuals differ | Compare | Semantic text overlap does not alone fail visual diversity; repeated style warning may be consciously acknowledged; near duplicate cannot |
| PC-AI07 | No history for new studio | Generate | AI still generates fresh complete composition; comparison says0recentposts, never falsely says compared10 |
| PC-AI08 | User chooses Make this post look different | Confirm regeneration | AI selects new concept automatically, no manual brief; relevant approval invalidated; old assets/render and authorized schedule snapshot preserved |
| PC-AI09 | AI Reel script/storyboard complete, no encodedMP4 | Open library | Not Ready for review; visuals/audio/render/validation remain; only validated30–40sec1080×1920MP4is complete Reel |
| PC-R24-01 | Server accepts research at2026-10-08T19:00Z | Run Last24hours | Window fixed2026-10-07T19:00Zto2026-10-08T19:00Z; Chicago display14:00to14:00; later retry does not drift window |
| PC-R24-02 | One article published25hoursago but crawled1hourago | Research completes | Excluded from verified24hourfeed; visible historical/excluded record with publication/capture dates; not ranked as fresh |
| PC-R24-03 | Run captures100findings,24firstpage,20duplicates,7excluded | Open Allfindings and paginate | All100records reachable by disposition; no hidden top10limit; duplicate groups expandable; stable unique IDs |
| PC-R24-04 | Findings priorities95,80,80 with different dates | Open Discover | Descending95then80; tied80newer publication first then stableID; Why ranked here reveals weighted dimensions and policy |
| PC-R24-05 | Source publication date unknown | Complete research | Dateunverifiedsegment visible; not included in verified24hourcount; no false New badge |
| PC-R24-06 | Daily run crosses DST transition | Calculate past1day | Exactly24hoursUTC, displayoffsets correctly; not23or25hours; schedule DST ambiguity still resolved separately |
| PC-R24-07 | Ranked topic chosen; Bothselected | Generate and approveCarouselonly | Independent fullimage/Reeljobs; Carouselapproved; Reelunapproved; only approvedCarouselmay reach publicationconfirmation |
| PC-R24-08 | Contentapproved, Instagramconnected | Finish approval | ApprovedstateandPublish/Scheduleaction visible; no automaticpost until explicitselectedaccount/version/timeauthorization |
