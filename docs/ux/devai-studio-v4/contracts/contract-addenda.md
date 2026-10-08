# Exact resource and mutation addenda

All /v1 endpoints in this document are proposed; none is asserted to exist. This supplement resolves operations more granular than required-contracts.md. All responses follow shared Error/Page schema and workspace checks. All mutation payloads accept expectedRevision except public auth, uploads/create, or explicit job revision. Idempotency-Key on accepted work;204for deletes,200for resource updates,202with jobId for durable work.429includes Retry-After;413returns media-size error without discarding draft;415unsupported type. PUT/PATCHreturn revisioned resource.

| Resource | Read contract | Response/behavior |
|---|---|---|
| Home | GET /v1/home | resumeOutputs,reviewCount,activeJobs,researchHealth,recentActivity; counts own permitted workspace |
| Discover/queue/topic | GET /v1/topics?q=&category=&saved=&status=&cursor= and GET /v1/topics/{id} |24items stable cursor; topic includes source snapshot IDs, angle, selected and saved; no boolean truth claim |
| Evidence | GET /v1/topics/{id}/sources; GET /v1/sources/{snapshotId}; GET /v1/outputs/{id}/claims | Cached immutable excerpt/publishedAt/capturedAt/canonicalURL/humanReview and quote ranges |
| Setup | GET /v1/setups/{id}; GET /v1/providers/capabilities | Capability revision checked again at generation; estimated units not fictitious cost |
| Content/library | GET /v1/content?q=&status=&format=&sort=&cursor=; GET /v1/content/{id} | Independent output IDs/revisions, retained published/scheduled snapshots |
| Carousel | GET /v1/outputs/{id}; GET /v1/outputs/{id}/slides | Current inputs and asset hashes, stale reasons and generation jobs |
| Reel | GET /v1/outputs/{id}/timeline; GET /v1/outputs/{id}/renders; GET /v1/renders/{id} | Scene source ranges, cues, mix, currentness; MP4 rendered/validated distinction |
| Versions | GET /v1/outputs/{id}/versions?cursor=; GET /v1/outputs/{id}/versions/{revision} | Immutable actor/time/input/media snapshots; restore creates new head |
| Review | GET /v1/review?format=&status=&q=&cursor=; GET /v1/outputs/{id}/review | One row per output; current checklist eligibility and approval snapshots |
| Publication/calendar | GET /v1/publications/{id}; GET /v1/publications?from=&to=&timeZone=&cursor= | Explicit frozen approval account and attempts; calendar bounds converted server-side |
| Activity | GET /v1/jobs?status=&type=&cursor=; GET /v1/jobs/{id} |100? No: target page24rows; cursor independent of current legacy last100 limit; serverTime/heartbeat/unit states |
| Inbox | GET /v1/notifications?read=&cursor= | Durable deduplicated eventID and authorized deep link |
| Analytics | GET /v1/analytics?accountId=&from=&to=&timeZone=&format=; GET /v1/publications/{id}/metrics | Nullable metric, missingReason,denominator,coverage,lastFetched; definitions from current capability catalog |
| Settings | GET /v1/me; GET /v1/workspaces/{id}/settings; GET /v1/providers; GET /v1/instagram/accounts; GET /v1/sessions; GET /v1/workspaces/{id}/members | Secure masked presence, permission/capability details; never plaintext keys |
| Help/search | GET /v1/help?q=; GET /v1/help/articles/{slug}; GET /v1/search?q=&scope= | Help version + article text; global search only indexed authorized topics/content/jobs, max5per group |

## Supplemental mutation contracts

| Operation | Exact request | Result |
|---|---|---|
| PATCH /v1/topics/{id}/sources/{sourceId} | excerpt,publishedAt?,reviewNote,expectedRevision | New immutable snapshotId; recalculate claims, invalidate dependent approvals and block dependent schedules; no mutation of old excerpt |
| PATCH /v1/setups/{id} | formats,options,expectedRevision | Saved config revision; no generation |
| PATCH /v1/outputs/{id}/caption | caption,hashtags,expectedRevision | Relevant approval invalidated; video render unchanged when timeline unchanged |
| POST /v1/outputs/{id}/caption/suggestions | expectedRevision,brief | suggestionId,baseRevision,candidateCaption; Apply PATCH only if base current |
| POST /v1/outputs/{id}/script/suggestions | expectedRevision,sceneIds,brief | Proposed script diff; no saved script changes until Apply |
| POST /v1/outputs/{id}/voiceover | expectedRevision,scriptHash,voiceId,confirmed:true |202job+audioAsset input hash; output state generating audio; retain previous audio |
| POST /v1/outputs/{id}/subtitles | expectedRevision,audioHash,language |202alignment job, cue suggestions; Apply confirmed cues creates timeline revision |
| POST /v1/outputs/{id}/audio/uploads | fileName,mimeType,sizeBytes,license |uploadId,signedURL,expiresAt,maxBytes; WAV/MP3/M4A<=50MiB |
| POST /v1/uploads/{uploadId}/complete | byteHash,sizeBytes |202decode/scan job; only validated ready asset usable; expired upload restart maintains draft |
| POST /v1/publications/{id}/resume | expectedRevision,mode,scheduledLocal?,timeZone?,confirmationId | New explicit authorization after credential recovery; no implicit missed-slot catch-up |
| PATCH /v1/workspaces/{id}/settings | expectedRevision,researchEnabled,researchLocalTime,timeZone,categories,autoDraftOptions | Confirmed nextRunAt and worker health; auto draft explicit capability/estimated-unit consent; never auto publish |
| PATCH /v1/notification-preferences | expectedRevision,eventChannels,quietHours,timeZone | Quiet hours delay normal pushes; unknown/failed publication notification urgent; inbox immediate |
| PUT /v1/devices | pushToken,platform,deviceId,locale | Register user-scoped token; revoke on logout |
| PATCH /v1/me | displayName,locale,timeZone,avatarAssetId?,expectedRevision | Revisioned profile; timezone does not reinterpret existing reservations |
| POST /v1/me/avatar/uploads | fileName,mimeType,sizeBytes |<=5MiBJPEG/PNG; stripEXIF/crop on complete; replace via PATCH /me |
| POST /v1/me/apple | identityToken,nonce,recentAuthProof | Verified identity linked; no account enumeration or hidden merge |
| POST /v1/workspaces/{id}/invitations | email,role,publishPermission:false | Invite7daytoken; resend/revoke explicit POST /{inviteId}/resend and DELETE /{inviteId} |
| POST /v1/diagnostics/exports | entityId?,includeRedactedLogs:true | Job produces sanitized JSON; requestIDs and stage errors, never secrets/source tokens/local paths |
| POST /v1/analytics/refresh | accountId,range | Durable refresh with account rate limit; cached values stay labeled |
| POST /v1/analytics/exports | accountId,range,postIds,metricIds,fileType:csv or pdf | Export job returns expiring download; null reasons/coverage retained |
| POST /v1/content/{id}/exports | outputIds,revision,fileType:zip | Immutable asset bundle and evidence/caption manifest |
| GET /v1/outputs/{id}/exports/{revision} | read only | Authenticated expiring download of selected revision; native share action |
| DELETE /v1/account/deletion | recentAuthProof | Cancel pending deletion before effectiveAt; data/export preserved |

## Legacy adapter boundaries

Do not call current single-post approval endpoints for Reel. Carousel-only compatibility may map proposed /outputs/{id}/submit,approve,changes to existing /posts/{id}/submit,approve,reject if no advanced review note contract is needed; independent format and source snapshot behavior requires new models first. Legacy edits have no CAS and cannot support safe cross-device autosave until adapter persists/rejects expected revision. Legacy per-slide regeneration accepts no creative brief; use new saved brief contract before exposing that feature. Existing /topics/generate supports carousel6–8only and returns job or existingpost; setup Both requires new orchestration. Existing export ZIP route preserves carouselassets but newmanifest/Reel export requires new code. Legacy static workflow config does not save schedules or credentials. Current /reconcile uses published:boolean and note; Still unknown is no mutation; adapt explicit outcomes only when externallyconfirmed. Shared X-API-Key is a development gateway, not production email/Apple auth.

URL-only intake: POST /v1/ideas `{url,category,priority}`→202ideaId/jobId; GET /v1/ideas/{id}→state,url,sourceCandidate,excerptCandidate,publishedAtCandidate,capturedAt,issues,duplicateTopicId?; POST /v1/ideas/{id}/confirm `{expectedRevision,title,source,excerpt,publishedAt?,category,priority,humanReviewed:true}`→topicId. Same normalized URL active key deduplicates extraction. Unsupported/password/paywall page may fail; user-provided excerpt fallback, no simulated verification. Extraction job uses generic JOB cancellation/retry. URLidea is separate from /v1/topics editorial topic until human review.
