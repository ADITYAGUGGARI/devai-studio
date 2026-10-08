# Existing API mapping

All routes below inspected in api/src/devai/routes. Current protected requests use X-API-Key. Media token route and /health are exceptions. Authentication changes are required before public production. These routes are preserved/adapted; /v1 examples in the next file are proposed, not existing.

| UI control | Existing operation | Payload / result / limits |
|---|---|---|
| run-research | POST /research/daily/run | 202 Job; date/timezone deduplicated; daily mode from server config |
| refresh | POST /research/refresh | 202 Job; one active research key |
| add-source | POST /topics | 201 Topic; title/url/excerpt/source/category/published_at/priority; duplicate 409 |
| select-topic | POST /topics/{id}/select | Persists one selected queued topic across reloads |
| priority | PATCH /topics/{id} | priority integer 0–100; blocked for used/generating topic |
| category | PATCH /topics/{id} | news/tutorial/architecture/tools/insight |
| archive-topic | PATCH /topics/{id} | status archived; selection cleared |
| restore-topic | PATCH /topics/{id} | status queued |
| edit-evidence | PATCH /topics/{id} | excerpt 240–10,000; verification resets |
| verify-evidence | POST /topics/{id}/verify | Human acknowledgment; queued topic only |
| start-generation | POST /topics/{id}/generate | slide_count 6–8 and artwork; 202 Job OR existing post_id; Reel/Both require new contract |
| slide-copy | PATCH /posts/{id}/slides/{slide_id} | headline/body; invalidates approval and image validation; lacks concurrency precondition |
| caption-text | PATCH /posts/{id} | caption; invalidates entire legacy post approval |
| regenerate-slide | POST /posts/{id}/slides/{slide_id}/regenerate | 202 Job; no custom prompt argument currently |
| regenerate-confirm | POST /posts/{id}/slides/{slide_id}/regenerate | Legacy regeneration ignores future freeform brief until contract extended |
| submit-review | POST /posts/{id}/submit | draft/rejected → pending_review; active-job lock |
| approve | POST /posts/{id}/approve | pending_review → approved; current validated native images and evidence required |
| submit-changes | POST /posts/{id}/reject | Legacy rejected status; no feedback fields; extension required |
| confirm-publish | POST /posts/{id}/publish | 202 immutable approved carousel job; single configured account only; no scheduling |
| save-outcome | POST /posts/{id}/reconcile | published boolean, external_id if true, note 10–1000; publishing and idle required |
| retry-job | POST /jobs/{id}/retry | failed/retry_wait non-publish only; stale version and active job guards |
| download | GET /posts/{id}/export | Carousel ZIP; actual PNG, caption, sources and review; Reel download requires new contract |
| export-content | GET /posts/{id}/export | Carousel only; current native assets required |
| view-job | GET /jobs/{id} | Durable job; stage, progress, attempts, safe error and result |
| job-open | GET /jobs/{id} | Durable job; no cancel or heartbeat field in public response |
| activity | GET /posts/{id}/audit | Chronological event list; actor field missing |
| open-draft | GET /posts/{id} | Post and evidence; one legacy carousel only |
| content-open | GET /posts/{id} | Post and evidence; future content wrapper needed |
| open-editor | GET /posts/{id} | Do not permit edits while active post job |
| search-topics | GET /topics + client filter | Existing endpoint returns all; server pagination/search extension required |
| search-content | GET /posts + client filter | Existing endpoint returns all; server pagination/search extension required |

Read operations: GET /posts, GET /posts/{id}, GET /topics, GET /jobs (latest 100), GET /jobs/{id}, GET /workflow/config, GET /research/daily/latest, GET /posts/{id}/audit, GET /posts/{id}/publishing, GET /posts/{id}/slides/{slide_id}/image. Daily latest preserves dated run + latest_research. Media GET /media/{token}.jpg serves approved immutable JPEGs. Legacy /editorial routes remain compatibility-only; future UI uses unified /topics. Existing POST /research/generate and /research/draft are legacy paths, not the preferred durable setup flow.

Existing models: Post(id,title,caption,status,string version,created,verification_json); Slide(id,post_id,position,headline,body,visual_direction,artwork_path,composition_mode,validation_json,content_hash); ArticleEvidence(source URL/title/name/excerpt/published/retrieved/topic/angle); Topic(status,verification,selected,priority,category,url,post_id,job_id,error); Job(status,kind,payload/result,attempts,active/schedule keys,lease); PublishAttempt(version,status,external_id,error); MediaAsset(token,post,version,slide,path,sha256); Audit(event,created). Approval is currently represented by Post status/version and validation checks, not a new separate multi-format Approval entity.

Error adapter required: do not stringify JSON validation array into generic “Request failed.” Map HTTP 401 auth recovery, 403 access, 404 unavailable, 409 entity/state/revision mismatch, 422 field errors, 429 retry-after, 503 unavailable capability. Existing endpoints may return different string detail; compatibility adapter keeps actionable human messages without claiming a new error envelope already exists. GET image blob downloads remain authenticated and object URLs revoked when replaced/unmounted.
