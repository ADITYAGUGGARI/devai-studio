# Shared controls and interaction contracts

| ID | Control | Trigger | Result / recovery | API | Accessibility |
|---|---|---|---|---|---|
| GLOBAL-01 | Wordmark | Activate brand | Navigate /home; native selects Home tab and preserves other stacks | GET current Home aggregates | heading focus,link semantics |
| GLOBAL-02 | Global search | Cmd/Ctrl+K or named search control | Open query overlay; topics/content/jobs grouped;300ms debounce; abort stale reads; Enter opens selected result; Escape returns focus | Proposed GET /v1/search?q=&scope= | combobox/listbox keyboard; labeled native search sheet |
| GLOBAL-03 | Notifications bell | Click/Enter/native tap | Open /notifications; unread badge semantic; no unread mutation until item opened/read | Proposed GET /v1/notifications | 44px/pt; label includes unread count |
| GLOBAL-04 | Avatar menu | Click/Enter/native tap | Profile/Security/Sign out actions; Escape returns invoker; sign-out respects unsynced buffer | profile/session contracts | menu keyboard or native sheet |
| GLOBAL-05 | Sidebar collapse/drawer | Click/Enter/native tap | Expanded232/collapsed72 web preference; narrow view drawer retains labels; Escape restores hamburger focus | Local device preference | navigation landmark; no hidden-only routes |
| GLOBAL-06 | Tab navigation | Tap native labeled tab | Home/Discover/Content/Activity/Settings preserve independent navigation stack and scroll; repeated tap scrolls root top only deliberately | Fetch authorized current tab data | native tab traits; VoiceOver selected;44pt target |
| GLOBAL-07 | Clear filters | Click/Enter/native tap | Clear query/category/status/date/account filters to list defaults; reset cursor; cached results retained while updating | query contract | announce filter reset; focus returns toolbar |
| GLOBAL-08 | Move before/after | Click/Enter/native action | Choose stable target asset ID and atomic ordered-ID update; equivalent to drag; update visual order and invalidate affected baked artwork | Proposed PUT /v1/outputs/{id}/slide-order or /scene-order | named ordinal; keyboard and VoiceOver action |
| GLOBAL-09 | Conflict resolve | Choose Mine/Server/manual merge; Save | Compare field deltas against base; explicit CAS write on Save; repeat409 keeps local buffer; cancel never overwrites | revision-aware PATCH output contract | side-by-side desktop; stacked native; focus first unresolved field |
| GLOBAL-10 | Native Done/Back | Tap/back gesture/Escape overlay | Saved editor closes to originating Content entity; unacknowledged buffer opens D-UNSAVED; never cancels durable job | read authoritative entity before resume | focus/VoiceOver route title; keyboard avoidance |

Each pending mutation disables only its own action; 401 reauth,403 read-only,409 resolve,422 inline,network retains buffer. List navigation never spends generation credits or authorizes publishing. Toast close dismisses transient surface only,never deletes inbox event; banners with mandatory recovery remain persisted. Empty/skeleton controls cannot suggest unavailable backend capabilities. Native sheet swipe/Close is Cancel while dirty form uses D-UNSAVED. Calendar swipe changes date only; content-row swipe Archive has visible menu alternative and active-publication lock.


## Native contextual tools — visual revision 4

A contextual More control on a child view opens the applicable tools sheet using that screen’s existing controls, not a new backend operation. The tools-continuation artboards show scroll content or the appropriate contextual presentation; they are not additional required wizard steps. Hide actions failing the documented role/state eligibility or show their precise disabled reason. Destructive, paid and publication actions always open the existing confirmation before mutation. Closing restores focus, selected entity and scroll. Back never silently discards the protected buffer. Existing navigation conventions and gesture equivalents remain unchanged.
