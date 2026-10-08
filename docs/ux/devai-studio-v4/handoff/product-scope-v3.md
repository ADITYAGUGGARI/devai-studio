# Authoritative product scope — revision 3

The latest requirements add to the previous scope. Nothing in desktop/iOS, workflows A–O, authentication/settings, sources/claims, editors, library/jobs/notifications, scheduling, analytics, accessibility or cross-device recovery is removed. The full requirement matrix remains the delivery checklist. This document clarifies the central daily editorial product and supersedes older discovery defaults that mixed undated/older sample ideas with current news.

## Main loop

1. Research AI developments relevant to software engineering over the past 24 hours.
2. Show all researched findings, ranked highest priority first, with source evidence and ranking explanations.
3. Choose a topic; AI generates complete carousel images, a complete Reel or both without layout/background instructions.
4. Review the actual media, captions and source-supported claims; request changes or approve each format independently.
5. Explicitly authorize publication or scheduling to the selected connected Instagram account.
6. Report the publication outcome, retain media/history and analytics, and recover failures without duplicate posts or lost work.

The user can browse every finding in a research run, not only the highest-ranked suggestions. A publication approval is not combined with creative generation. Approved content can be published only after the explicit account/version/time confirmation described in the publication contracts. Research and generation never publish automatically.

## Research scope and time semantics

Default window is rolling 24 hours: windowStartUTC = acceptedAtUTC minus 24 hours; windowEndUTC = acceptedAtUTC. The exact window stays frozen for the run. The selected timezone changes displayed dates, not the duration. Daily scheduled runs use their scheduled instant; manual runs use server acceptance time. 'Past 1 day' is therefore not midnight-to-midnight, and a DST day does not expand/shrink the window. Show 'Last 24 hours', local start/end and timezone. Optional historical window is separate, visibly labeled, and does not contaminate the daily feed.

Research categories: model/API releases useful for development; coding agents and assistants; frameworks, SDKs and developer tools; architecture/infrastructure; evaluation/testing/observability; deployment and runtime reliability; security/privacy; open-source engineering; practical tutorials and research with concrete developer implications. Exclude unrelated consumer/celebrity/general business AI unless a documented engineering impact makes it relevant.

Source strategy: official release notes/documentation/changelogs, maintainers' repositories/releases, primary research, official engineering blogs and reputable independent technical reporting for corroboration. Track each source's attempt, access result, publication timestamp and captured timestamp. Exact source URL and immutable excerpt required before supported-fact content generation. Retrieved recently does not mean published recently. Unknown publication date is shown as 'Date unverified' in a separate findings segment, excluded from the main verified-24-hour count; it is not discarded invisibly. Updated articles enter the run only if substantive update timestamp and changed content are verified; original publication date remains visible.

Do not claim exhaustive coverage of the internet. Product copy reports actual coverage: '24 sources checked · 18 findings · 3 source failures'. Research History reveals checked/skipped/failed sources and run limitations. 'All findings' means all findings captured by that run, including lower-ranked items and duplicate groups; no hidden top-N cap. Each accepted run retains raw findings and duplicates even if only some become usable editorial topics.

## Ranking (initial product rule)

Each finding receives a server-calculated priority score 0–100 with versioned ranking policy. Weighted dimensions, each normalized 0–1: developer relevance25, practical impact20, source strength20, recency15, novelty10, evidence completeness10. Priority = round(sum(weight × dimension)). Explain each dimension in 'Why ranked here', alongside concise AI rationale labeled interpretation. Do not fabricate social popularity or impact statistics. Missing evidence lowers evidence/source strength; it never becomes a truth badge. Recency uses verified publication/update time, not crawling time.

Default sort: effectivePriority descending, verifiedPublishedAt descending, stable findingId ascending. Manual editorial priority override is explicit, retained with actor/time and badge 'Priority adjusted'; it does not change the original computed score. Search/filter/sort applies to all run findings with stable cursors. Historical ranking snapshots do not reshuffle silently when new evidence arrives; show a newer ranking available and refresh explicitly, preserving selected finding and filters. Suggested 'Top opportunities' is a subset linked to the full results, not a replacement for them.

Duplicate handling groups canonical URL duplicates and semantic reports of the same event. The primary topic links every corroborating source; users can expand grouped findings. Updated information appends evidence to a new snapshot and flags existing drafts for review. Previously used topics link to prior content; generating another treatment is an explicit new draft, not accidental duplication. Lower relevance is still visible through All findings or Excluded/Needs evidence filters with reason.

## Discover and research result designs

DISC-01 default: 'Developer AI news · Last 24 hours'; latest completed run timestamp, coverage summary and Run research/View active run. Toolbar Search, category, priority, evidence status, Saved and run selection. Default priority descending. Each row contains title, score, rank, verified publication time, source identity/count, evidence status, one-line developer relevance, Open topic and Save. Thumbnail only if a legitimate source thumbnail or existing generated output exists; don't fabricate an already-generated post before generation.

Run progress opens ACT-02 with immutable time window, source coverage, extraction/verification/dedup/ranking stages, unit counts and preserved partial findings. Queued/running/partial/completed/no-new/failed/stalled/cancelling/cancelled each has the treatment specified in job contracts. 'View available findings' is enabled as verified findings arrive; it never claims the run complete. Research History in Discover lists every run and frozen score policy. All findings includes usable, date-unverified, duplicate and excluded records with reasons. No usable findings offers Retry failed sources or Add custom topic; all duplicates is a completed no-new-results run.

TOPIC-01 includes headline, time, source evidence, developer relevance, priority explanation, saved state, previous content and Create Carousel/Create Reel/Create Both options. Choice opens the shared format/setup summary. No manual visual idea is required. Source inspection and claim resolution remain available before and during generation/review.

## Proposed API additions; not existing endpoints

POST /v1/research/runs `{window:'last_24_hours',categoryIds,rankingPolicyRevision,sourceCatalogRevision}` →202runId/jobId/windowStartUTC/windowEndUTC. Same active-window/catalog key returns existing run unless explicit new run intent authorized. GET /v1/research/runs?cursor= →history. GET /v1/research/runs/{runId} →status/window/coverage/partialCounts/rankingPolicy/lastHeartbeat. GET /v1/research/runs/{runId}/findings?q=&category=&evidence=&priorityMin=&sort=&cursor= →24row stable Page with findings and total counts by disposition; raw/duplicate/excluded records retained. GET /v1/findings/{id} →source snapshots, topicId?, duplicateGroupId, dimensions/score/explanation/disposition. PATCH /v1/topics/{id}/priority-override `{expectedRevision,priority|null,reason}` →actor/time override without mutating computed score. POST /v1/research/runs/{runId}/retry-sources `{sourceIds,expectedJobRevision}` →safe scoped job preserving verified results. PATCH /v1/workspaces/{id}/settings stores categories, rolling-window rule, timezone and daily schedule; scheduler/worker health must confirm effectiveness.

Legacy /research/refresh and /research/daily/run can remain compatibility routes but do not magically implement these full-history/ranking/coverage contracts. Existing priority0–100 is not evidence that the proposed ranking dimensions and last-24-hour discovery behavior work. Preserve durable jobs and saved evidence while extending the model.

## Additional supporting experience (retained scope)

Saved topics and editorial queue; transparent source/claim review; custom URL and excerpt intake; AI creative history and varied-background checks; per-slide/scene recovery; factual copy edits; versions/undo/conflicts/autosave; completed MP4 validation; independent format approval; caption/hashtag review; selected-account preflight; scheduling/DST/credential recovery; uncertain publish reconciliation; exports/Trash; account/provider/settings/security; activity/inbox/push; analytics with unavailable-data treatment; native scene editing; cross-device continuation. All earlier requirements remain mapped in qa/requirement-areas.csv and acceptance cases.
