# Final operation index revision3

/v1 routes are proposed; local controls have no invented mutation. Schemas: contract-addenda.md,product-scope-v3.md,ai-creative-autopilot.md.

| Interaction | Control | Operation | Payload | Next destination |
|---|---|---|---|---|
|AUTH-01-I01|email|None on input; owning form Save contract|trim; syntactic email; autofill=email|/sign-in|
|AUTH-01-I02|send-code|POST /v1/auth/email/challenges|{email,returnTo}|AUTH-02 with returned challengeId|
|AUTH-01-I03|apple-signin|POST /v1/auth/apple|{identityToken,nonce,authorizationCode}|Remain on /sign-in with acknowledged revision/state; no implicit publication or navigation|
|AUTH-01-I04|help|None: local UI/navigation; destination resource read only|No payload|HELP-01|
|AUTH-02-I01|code|None on input; owning form Save contract|6numeric digits; one input; oneTimeCode|/sign-in/verify|
|AUTH-02-I02|verify-code|POST /v1/auth/email/verify|{challengeId,code}|ONB-01 if no workspace; otherwise validated returnTo or HOME-01|
|AUTH-02-I03|resend|POST /v1/auth/email/challenges|{email,replaceChallengeId}|Remain on /sign-in/verify with acknowledged revision/state; no implicit publication or navigation|
|AUTH-02-I04|change-email|None: local UI/navigation; destination resource read only|No payload|AUTH-01|
|ONB-01-I01|workspace-name|None on input; owning form Save contract|1–80characters; trimmed|/onboarding|
|ONB-01-I02|timezone|None on input; owning form Save contract|searchable IANA zone; do not reinterpret existing reservations|/onboarding|
|ONB-01-I03|language|None on input; owning form Save contract|English initial release; other choices disabled with explanation|/onboarding|
|ONB-01-I04|research-toggle|None on input; owning form Save contract|off default; saving activates next run, not immediate run|/onboarding|
|ONB-01-I05|finish-onboarding|POST /v1/workspaces|{name,timeZone,locale,researchEnabled:false}|HOME-01 in returned workspace|
|HOME-01-I01|review-count|None: local UI/navigation; destination resource read only|No payload|REVIEW-01|
|HOME-01-I02|active-job|None: local UI/navigation; destination resource read only|No payload|ACT-02|
|HOME-01-I03|continue-edit|None: local UI/navigation; destination resource read only|No payload|/home|
|HOME-01-I04|discover|None: local UI/navigation; destination resource read only|No payload|DISC-01|
|HOME-01-I05|run-research|POST /v1/research/runs|{window:last_24_hours,categoryIds,rankingPolicyRevision,sourceCatalogRevision}|ACT-02 job detail; DISC-01?run=:runId for findings|
|HOME-01-I06|add-topic|None: local UI/navigation; destination resource read only|No payload|IMPORT-01|
|DISC-01-I01|search-topics|GET /v1/research/runs/{runId}/findings?q=&category=&evidence=&priorityMin=&sort=&cursor=|Immutable runId and filter/query state; default priority descending;24itemcursorpage|/discover|
|DISC-01-I02|saved-tab|GET /v1/research/runs/{runId}/findings?q=&category=&evidence=&priorityMin=&sort=&cursor=|Immutable runId and filter/query state; default priority descending;24itemcursorpage|/discover|
|DISC-01-I03|filters|GET /v1/research/runs/{runId}/findings?q=&category=&evidence=&priorityMin=&sort=&cursor=|Immutable runId and filter/query state; default priority descending;24itemcursorpage|/discover|
|DISC-01-I04|topic-open|None: local UI/navigation; destination resource read only|No payload|TOPIC-01|
|DISC-01-I05|save-topic|PUT /v1/topics/{topicId}/saved|{saved:!currentSaved}|Remain on /discover with acknowledged revision/state; no implicit publication or navigation|
|DISC-01-I06|load-more|GET /v1/research/runs/{runId}/findings?q=&category=&evidence=&priorityMin=&sort=&cursor=|Immutable runId and filter/query state; default priority descending;24itemcursorpage|/discover|
|DISC-01-I07|refresh|POST /v1/research/runs|{window:last_24_hours,categoryIds,rankingPolicyRevision,sourceCatalogRevision}|ACT-02 job detail; DISC-01?run=:runId for findings|
|QUEUE-01-I01|select-topic|POST /topics/{topicId}/select|{}|Remain on /discover/queue with acknowledged revision/state; no implicit publication or navigation|
|QUEUE-01-I02|priority|PATCH /topics/{topicId}|{priority:0..100} or {category:enum}|Remain on /discover/queue with acknowledged revision/state; no implicit publication or navigation|
|QUEUE-01-I03|category|PATCH /topics/{topicId}|{priority:0..100} or {category:enum}|Remain on /discover/queue with acknowledged revision/state; no implicit publication or navigation|
|QUEUE-01-I04|archive-topic|PATCH /topics/{topicId}|{status:archived|queued}|Remain on /discover/queue with acknowledged revision/state; no implicit publication or navigation|
|QUEUE-01-I05|restore-topic|PATCH /topics/{topicId}|{status:archived|queued}|Remain on /discover/queue with acknowledged revision/state; no implicit publication or navigation|
|QUEUE-01-I06|topic-open|None: local UI/navigation; destination resource read only|No payload|TOPIC-01|
|TOPIC-01-I01|topic-tabs|None: local UI/navigation; destination resource read only|No payload|/topics/:topicId|
|TOPIC-01-I02|save-topic|PUT /v1/topics/{topicId}/saved|{saved:!currentSaved}|Remain on /topics/:topicId with acknowledged revision/state; no implicit publication or navigation|
|TOPIC-01-I03|open-source|None: local UI/navigation; destination resource read only|No payload|/topics/:topicId|
|TOPIC-01-I04|edit-angle|PATCH /v1/topics/{topicId}/angle|{expectedRevision,editorialAngle}|Remain on /topics/:topicId with acknowledged revision/state; no implicit publication or navigation|
|TOPIC-01-I05|create|None: local UI/navigation; destination resource read only|No payload|CREATE-01|
|TOPIC-01-I06|open-draft|None: local UI/navigation; destination resource read only|No payload|LIB-02|
|SOURCE-01-I01|source-select|None: local UI/navigation; destination resource read only|No payload|/topics/:topicId/sources|
|SOURCE-01-I02|open-source|None: local UI/navigation; destination resource read only|No payload|/topics/:topicId/sources|
|SOURCE-01-I03|edit-evidence|PATCH /v1/topics/{topicId}/sources/{sourceId}|{expectedRevision,excerpt,publishedAt,reviewNote}|Remain on /topics/:topicId/sources with acknowledged revision/state; no implicit publication or navigation|
|SOURCE-01-I04|verify-evidence|POST /topics/{topicId}/verify|{}|Remain on /topics/:topicId/sources with acknowledged revision/state; no implicit publication or navigation|
|CLAIM-01-I01|claim-open|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/claims|
|CLAIM-01-I02|evidence-jump|None: local UI/navigation; destination resource read only|No payload|SOURCE-01|
|CLAIM-01-I03|edit-claim|PATCH /v1/outputs/{outputId}/claims/{claimId}|{expectedRevision,text} or {excluded:true,reason}|Remain on /content/:contentId/claims with acknowledged revision/state; no implicit publication or navigation|
|CLAIM-01-I04|exclude-claim|PATCH /v1/outputs/{outputId}/claims/{claimId}|{expectedRevision,text} or {excluded:true,reason}|Remain on /content/:contentId/claims with acknowledged revision/state; no implicit publication or navigation|
|CLAIM-01-I05|rerun-grounding|POST /v1/outputs/{outputId}/grounding|{expectedRevision}|Remain on /content/:contentId/claims with acknowledged revision/state; no implicit publication or navigation|
|IMPORT-01-I01|topic-title|None on input; owning form Save contract|5–500characters|/topics/new|
|IMPORT-01-I02|source-url|None on input; owning form Save contract|canonicalHTTPS; no credential/query secrets; duplicate normalized URL check|/topics/new|
|IMPORT-01-I03|publisher|None on input; owning form Save contract|1–200characters|/topics/new|
|IMPORT-01-I04|excerpt|None on input; owning form Save contract|240–10000characters; exact source excerpt; no generated filler|/topics/new|
|IMPORT-01-I05|published-date|None on input; owning form Save contract|optional RFC3339; show unknown rather than infer|/topics/new|
|IMPORT-01-I06|category|PATCH /topics/{topicId}|{priority:0..100} or {category:enum}|Remain on /topics/new with acknowledged revision/state; no implicit publication or navigation|
|IMPORT-01-I07|priority|PATCH /topics/{topicId}|{priority:0..100} or {category:enum}|Remain on /topics/new with acknowledged revision/state; no implicit publication or navigation|
|IMPORT-01-I08|add-source|POST /topics|{title,url,source,excerpt,published_at?,category,priority}|TOPIC-01 with returned topicId|
|CREATE-01-I01|format-carousel|None: local UI/navigation; destination resource read only|No payload|/create?topic=:topicId|
|CREATE-01-I02|format-reel|None: local UI/navigation; destination resource read only|No payload|/create?topic=:topicId|
|CREATE-01-I03|format-both|None: local UI/navigation; destination resource read only|No payload|/create?topic=:topicId|
|CREATE-01-I04|save-setup|POST /v1/setups|{topicId,formats,options}|Remain on /create?topic=:topicId with acknowledged revision/state; no implicit publication or navigation|
|CREATE-01-I05|next|POST /v1/setups|{topicId,formats,creativeMode:ai_autonomous,defaultOptions}|CREATE-03|
|CREATE-02-I01|audience|None on input; owning form Save contract|1–160characters|/create/:setupId/configure|
|CREATE-02-I02|tone|None on input; owning form Save contract|Clear / Analytical / Conversational / Editorial|/create/:setupId/configure|
|CREATE-02-I03|language|None on input; owning form Save contract|English initial release; other choices disabled with explanation|/create/:setupId/configure|
|CREATE-02-I05|slide-count|None on input; owning form Save contract|integer6–8|/create/:setupId/configure|
|CREATE-02-I06|duration|None on input; owning form Save contract|integer30–40sec; default35|/create/:setupId/configure|
|CREATE-02-I07|voiceover|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,voiceId|null}|Remain on /create/:setupId/configure with acknowledged revision/state; no implicit publication or navigation|
|CREATE-02-I08|music|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,musicAssetId,voiceGainDb,musicGainDb,ducking,license}|Remain on /create/:setupId/configure with acknowledged revision/state; no implicit publication or navigation|
|CREATE-02-I09|subtitles|None on input; owning form Save contract|on default for Reel; off allowed, measured render still required|/create/:setupId/configure|
|CREATE-02-I10|back|None: local UI/navigation; destination resource read only|No payload|/create/:setupId/configure|
|CREATE-02-I11|next|None: local UI/navigation; destination resource read only|No payload|/create/:setupId/configure|
|CREATE-03-I01|edit-setup|None: local UI/navigation; destination resource read only|No payload|/create/:setupId/review|
|CREATE-03-I02|start-generation|POST /v1/setups/{setupId}/generate|{expectedRevision,confirmedFormats,capabilityRevision}|GEN-01 for carousel, GEN-02 for Reel; Both retains separate output/job IDs|
|CREATE-03-I03|save-setup|POST /v1/setups|{topicId,formats,options}|Remain on /create/:setupId/review with acknowledged revision/state; no implicit publication or navigation|
|CREATE-03-I04|back|None: local UI/navigation; destination resource read only|No payload|/create/:setupId/review|
|GEN-01-I01|output-tab|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/generation|
|GEN-01-I02|view-job|None: local UI/navigation; destination resource read only|No payload|ACT-02|
|GEN-01-I03|open-editor|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/generation|
|GEN-01-I04|retry-unit|POST /v1/jobs/{jobId}/retry|{expectedJobRevision,unitId?,correctedConfiguration?}|Remain on /content/:contentId/generation with acknowledged revision/state; no implicit publication or navigation|
|GEN-01-I05|cancel-generation|POST /v1/jobs/{jobId}/cancel|{expectedJobRevision,reason}|Current generation screen remains with cancelling then retained partial assets|
|GEN-01-I06|library|None: local UI/navigation; destination resource read only|No payload|LIB-01|
|CAR-01-I01|slide-select|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/carousel|
|CAR-01-I02|slide-copy|PATCH /v1/outputs/{outputId}/slides/{slideId}|{expectedRevision,headline,body}|Remain on /content/:contentId/carousel with acknowledged revision/state; no implicit publication or navigation|
|CAR-01-I04|regenerate-slide|None: local UI/navigation; destination resource read only|No payload|CAR-03|
|CAR-01-I05|reorder|PUT /v1/outputs/{outputId}/slide-order|{expectedRevision,orderedIds}|Remain on /content/:contentId/carousel with acknowledged revision/state; no implicit publication or navigation|
|CAR-01-I06|add-slide|POST /v1/outputs/{outputId}/slides|{expectedRevision,afterSlideId,headline,body}|Remain on /content/:contentId/carousel with acknowledged revision/state; no implicit publication or navigation|
|CAR-01-I07|delete-slide|DELETE /v1/outputs/{outputId}/slides/{slideId}|{expectedRevision}|Remain on /content/:contentId/carousel with acknowledged revision/state; no implicit publication or navigation|
|CAR-01-I08|undo|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/carousel|
|CAR-01-I09|redo|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/carousel|
|CAR-01-I10|versions|None: local UI/navigation; destination resource read only|No payload|VER-01|
|CAR-01-I11|preview|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/carousel|
|CAR-01-I12|caption|None: local UI/navigation; destination resource read only|No payload|CAP-01|
|CAR-01-I13|submit-review|POST /v1/outputs/{outputId}/submit|{expectedRevision,assetHashes,evidenceHashes}|REVIEW-02 for this output format/revision|
|CAR-02-I01|slide-copy|PATCH /v1/outputs/{outputId}/slides/{slideId}|{expectedRevision,headline,body}|Remain on /content/:contentId/carousel/slides/:slideId with acknowledged revision/state; no implicit publication or navigation|
|CAR-02-I03|save-now|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/carousel/slides/:slideId|
|CAR-02-I04|regenerate-slide|None: local UI/navigation; destination resource read only|No payload|CAR-03|
|CAR-02-I05|back|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/carousel/slides/:slideId|
|CAR-03-I02|regenerate-confirm|POST /v1/outputs/{outputId}/slides/{slideId}/generate|{expectedRevision,confirmed:true}|Remain on /content/:contentId/carousel/regenerate/:slideId with acknowledged revision/state; no implicit publication or navigation|
|CAR-03-I03|cancel|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/carousel/regenerate/:slideId|
|VER-01-I01|version-select|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/versions|
|VER-01-I02|compare-version|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/versions|
|VER-01-I03|restore-version|POST /v1/outputs/{outputId}/restore|{expectedRevision,historicalRevision}|Remain on /content/:contentId/versions with acknowledged revision/state; no implicit publication or navigation|
|VER-01-I04|back|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/versions|
|REEL-01-I01|play|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel|
|REEL-01-I02|scrub|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel|
|REEL-01-I03|mute|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel|
|REEL-01-I04|fullscreen|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel|
|REEL-01-I05|script|None on input; owning form Save contract|script per scene1–1000characters|/content/:contentId/reel|
|REEL-01-I06|scene-select|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel|
|REEL-01-I07|reorder-scenes|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,scenes:[ordered scene objects]}|Remain on /content/:contentId/reel with acknowledged revision/state; no implicit publication or navigation|
|REEL-01-I08|add-scene|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,scenes:[ordered scene objects]}|Remain on /content/:contentId/reel with acknowledged revision/state; no implicit publication or navigation|
|REEL-01-I09|delete-scene|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,scenes:[ordered scene objects]}|Remain on /content/:contentId/reel with acknowledged revision/state; no implicit publication or navigation|
|REEL-01-I10|voiceover|None: navigation; target reads GET /v1/outputs/{outputId}/timeline|No mutation|REEL-05|
|REEL-01-I11|music|None: navigation; target reads GET /v1/outputs/{outputId}/timeline|No mutation|REEL-05|
|REEL-01-I12|subtitles|None: navigation; target reads GET /v1/outputs/{outputId}/timeline|No mutation|REEL-06|
|REEL-01-I13|render|POST /v1/outputs/{outputId}/render|{expectedRevision,timelineHash,confirmed:true}|Remain on /content/:contentId/reel with acknowledged revision/state; no implicit publication or navigation|
|REEL-01-I14|versions|None: local UI/navigation; destination resource read only|No payload|VER-01|
|REEL-01-I15|preview|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel|
|REEL-01-I16|submit-review|POST /v1/outputs/{outputId}/submit|{expectedRevision,assetHashes,evidenceHashes}|REVIEW-02 for this output format/revision|
|REEL-02-I01|script|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,scenes:[{id,script}]}|Remain on /content/:contentId/reel/script with acknowledged revision/state; no implicit publication or navigation|
|REEL-02-I02|ai-rewrite|POST /v1/outputs/{outputId}/script/suggestions|{expectedRevision,sceneIds,brief}|Remain on /content/:contentId/reel/script with acknowledged revision/state; no implicit publication or navigation|
|REEL-02-I03|save-now|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel/script|
|REEL-02-I04|back|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel/script|
|REEL-03-I01|scene-select|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel/scenes|
|REEL-03-I02|reorder-scenes|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,scenes:[ordered scene objects]}|Remain on /content/:contentId/reel/scenes with acknowledged revision/state; no implicit publication or navigation|
|REEL-03-I03|add-scene|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,scenes:[ordered scene objects]}|Remain on /content/:contentId/reel/scenes with acknowledged revision/state; no implicit publication or navigation|
|REEL-03-I04|delete-scene|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,scenes:[ordered scene objects]}|Remain on /content/:contentId/reel/scenes with acknowledged revision/state; no implicit publication or navigation|
|REEL-03-I05|back|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel/scenes|
|REEL-04-I01|scene-copy|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,scenes:[{id,script,durationSec}]}|Remain on /content/:contentId/reel/scenes/:sceneId with acknowledged revision/state; no implicit publication or navigation|
|REEL-04-I02|scene-duration|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,scenes:[{id,script,durationSec}]}|Remain on /content/:contentId/reel/scenes/:sceneId with acknowledged revision/state; no implicit publication or navigation|
|REEL-04-I04|regenerate-scene|POST /v1/outputs/{outputId}/scenes/{sceneId}/generate|{expectedRevision,confirmed:true}|Remain on /content/:contentId/reel/scenes/:sceneId with acknowledged revision/state; no implicit publication or navigation|
|REEL-04-I05|save-now|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel/scenes/:sceneId|
|REEL-04-I06|back|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel/scenes/:sceneId|
|REEL-05-I01|voice-preview|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel/audio|
|REEL-05-I02|voiceover|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,voiceId|null}|Remain on /content/:contentId/reel/audio with acknowledged revision/state; no implicit publication or navigation|
|REEL-05-I03|music|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,musicAssetId,voiceGainDb,musicGainDb,ducking,license}|Remain on /content/:contentId/reel/audio with acknowledged revision/state; no implicit publication or navigation|
|REEL-05-I04|upload-audio|POST /v1/outputs/{outputId}/audio/uploads|{fileName,mimeType,sizeBytes,license}|Remain on /content/:contentId/reel/audio with acknowledged revision/state; no implicit publication or navigation|
|REEL-05-I05|volume|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,musicAssetId,voiceGainDb,musicGainDb,ducking,license}|Remain on /content/:contentId/reel/audio with acknowledged revision/state; no implicit publication or navigation|
|REEL-05-I06|ducking|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,musicAssetId,voiceGainDb,musicGainDb,ducking,license}|Remain on /content/:contentId/reel/audio with acknowledged revision/state; no implicit publication or navigation|
|REEL-05-I07|rights|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,musicAssetId,voiceGainDb,musicGainDb,ducking,license}|Remain on /content/:contentId/reel/audio with acknowledged revision/state; no implicit publication or navigation|
|REEL-05-I08|save-now|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel/audio|
|REEL-05-I09|back|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel/audio|
|REEL-06-I01|cue-select|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel/subtitles|
|REEL-06-I02|cue-text|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,cues:[{id,text,startMs,endMs}],subtitleStyle}|Remain on /content/:contentId/reel/subtitles with acknowledged revision/state; no implicit publication or navigation|
|REEL-06-I03|cue-timing|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,cues:[{id,text,startMs,endMs}],subtitleStyle}|Remain on /content/:contentId/reel/subtitles with acknowledged revision/state; no implicit publication or navigation|
|REEL-06-I04|subtitle-style|PATCH /v1/outputs/{outputId}/timeline|{expectedRevision,cues:[{id,text,startMs,endMs}],subtitleStyle}|Remain on /content/:contentId/reel/subtitles with acknowledged revision/state; no implicit publication or navigation|
|REEL-06-I05|save-now|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel/subtitles|
|REEL-06-I06|back|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel/subtitles|
|CAP-01-I01|caption-text|PATCH /v1/outputs/{outputId}/caption|{expectedRevision,caption,hashtags}|Remain on /content/:contentId/caption/:format with acknowledged revision/state; no implicit publication or navigation|
|CAP-01-I02|hashtags|PATCH /v1/outputs/{outputId}/caption|{expectedRevision,caption,hashtags}|Remain on /content/:contentId/caption/:format with acknowledged revision/state; no implicit publication or navigation|
|CAP-01-I03|suggest-caption|POST /v1/outputs/{outputId}/caption/suggestions|{expectedRevision,brief}|Remain on /content/:contentId/caption/:format with acknowledged revision/state; no implicit publication or navigation|
|CAP-01-I04|copy-caption|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/caption/:format|
|CAP-01-I05|save-now|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/caption/:format|
|CAP-01-I06|back|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/caption/:format|
|PRE-01-I01|previous|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/preview/carousel|
|PRE-01-I02|next-slide|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/preview/carousel|
|PRE-01-I03|zoom|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/preview/carousel|
|PRE-01-I04|slide-select|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/preview/carousel|
|PRE-01-I05|download|GET /v1/outputs/{outputId}/exports/{revision}|no mutation; authenticated expiring download|Remain on /content/:contentId/preview/carousel with acknowledged revision/state; no implicit publication or navigation|
|PRE-01-I06|edit|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/preview/carousel|
|PRE-01-I07|close|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/preview/carousel|
|PRE-02-I01|play|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/preview/reel|
|PRE-02-I02|scrub|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/preview/reel|
|PRE-02-I03|mute|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/preview/reel|
|PRE-02-I04|fullscreen|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/preview/reel|
|PRE-02-I05|transcript|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/preview/reel|
|PRE-02-I06|download|GET /v1/outputs/{outputId}/exports/{revision}|no mutation; authenticated expiring download|Remain on /content/:contentId/preview/reel with acknowledged revision/state; no implicit publication or navigation|
|PRE-02-I07|edit|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/preview/reel|
|PRE-02-I08|close|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/preview/reel|
|REVIEW-01-I01|review-filters|None: local UI/navigation; destination resource read only|No payload|/review|
|REVIEW-01-I02|review-open|None: local UI/navigation; destination resource read only|No payload|REVIEW-02|
|REVIEW-01-I03|search-content|None: local UI/navigation; destination resource read only|No payload|/review|
|REVIEW-02-I01|preview|None: local UI/navigation; destination resource read only|No payload|/review/:contentId/:format|
|REVIEW-02-I02|sources|None: local UI/navigation; destination resource read only|No payload|SOURCE-01|
|REVIEW-02-I03|caption|None: local UI/navigation; destination resource read only|No payload|CAP-01|
|REVIEW-02-I04|checklist|None: local UI/navigation; destination resource read only|No payload|/review/:contentId/:format|
|REVIEW-02-I05|approve|POST /v1/outputs/{outputId}/approve|{expectedRevision,checklist,reviewedAssetIds,assetHashes,evidenceHashes}|Remain on /review/:contentId/:format with acknowledged revision/state; no implicit publication or navigation|
|REVIEW-02-I06|request-changes|None: local UI/navigation; destination resource read only|No payload|REVIEW-03|
|REVIEW-02-I07|edit|None: local UI/navigation; destination resource read only|No payload|/review/:contentId/:format|
|REVIEW-02-I08|back|None: local UI/navigation; destination resource read only|No payload|/review/:contentId/:format|
|REVIEW-03-I01|revision-target|None on input; owning form Save contract|one or more output units or Caption/Sources/Overall|/review/:contentId/:format/changes|
|REVIEW-03-I02|revision-note|None on input; owning form Save contract|10–2000characters|/review/:contentId/:format/changes|
|REVIEW-03-I03|submit-changes|POST /v1/outputs/{outputId}/changes|{expectedRevision,targets,note}|REVIEW-01 after acknowledged feedback|
|REVIEW-03-I04|cancel|None: local UI/navigation; destination resource read only|No payload|/review/:contentId/:format/changes|
|PUB-01-I01|account-select|None on input; owning form Save contract|eligible connected accountID only; show handle and capability, never auto-switch on failure|/content/:contentId/publish/:format|
|PUB-01-I02|publish-mode|None on input; owning form Save contract|Publish now / Schedule; explicit radio; mode change never submits|/content/:contentId/publish/:format|
|PUB-01-I03|schedule-date|None on input; owning form Save contract|future local>=5min after serverNow; reject DST gaps; choose offset at overlap|/content/:contentId/publish/:format|
|PUB-01-I04|timezone|None on input; owning form Save contract|searchable IANA zone; do not reinterpret existing reservations|/content/:contentId/publish/:format|
|PUB-01-I05|preflight|POST /v1/publications/preflight|{outputId,approvalId,accountId,mode,scheduledLocal,timeZone,offsetChoice}|Remain on /content/:contentId/publish/:format with acknowledged revision/state; no implicit publication or navigation|
|PUB-01-I06|confirm-publish|POST /v1/publications|{outputId,approvalId,accountId,mode,scheduledLocal?,timeZone?,offsetChoice?,confirmationId}|PUB-02 with returned publicationId|
|PUB-01-I07|confirm-schedule|POST /v1/publications|{outputId,approvalId,accountId,mode,scheduledLocal?,timeZone?,offsetChoice?,confirmationId}|PUB-02 with returned publicationId|
|PUB-01-I08|cancel|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/publish/:format|
|PUB-02-I01|view-account|None: local UI/navigation; destination resource read only|No payload|SET-07|
|PUB-02-I02|view-content|None: local UI/navigation; destination resource read only|No payload|LIB-02|
|PUB-02-I03|view-job|None: local UI/navigation; destination resource read only|No payload|ACT-02|
|PUB-02-I04|reconcile|None: local UI/navigation; destination resource read only|No payload|PUB-03|
|PUB-02-I05|back|None: local UI/navigation; destination resource read only|No payload|/publications/:publicationId|
|PUB-03-I01|outcome|None on input; owning form Save contract|Published / Not published / Still unknown; no preselection|/publications/:publicationId/reconcile|
|PUB-03-I02|external-id|None on input; owning form Save contract|required for Published; max200characters|/publications/:publicationId/reconcile|
|PUB-03-I03|reconcile-note|None on input; owning form Save contract|10–1000characters|/publications/:publicationId/reconcile|
|PUB-03-I04|save-outcome|POST /v1/publications/{publicationId}/reconcile|{expectedRevision,outcome,externalId?,note}|PUB-02 with authoritative reconciled outcome|
|PUB-03-I05|cancel|None: local UI/navigation; destination resource read only|No payload|/publications/:publicationId/reconcile|
|CAL-01-I01|calendar-view|None: local UI/navigation; destination resource read only|No payload|/calendar|
|CAL-01-I02|calendar-date|None: local UI/navigation; destination resource read only|No payload|/calendar|
|CAL-01-I03|publication-open|None: local UI/navigation; destination resource read only|No payload|/calendar|
|CAL-01-I04|reschedule|PATCH /v1/publications/{publicationId}/schedule|{expectedRevision,scheduledLocal,timeZone,offsetChoice,confirmationId}|CAL-01 selected new date after explicit authorization ACK|
|CAL-01-I05|cancel-schedule|POST /v1/publications/{publicationId}/cancel|{expectedRevision,confirmed:true}|CAL-01 or invoking publication detail with Cancelled only after atomic ACK|
|CAL-01-I06|timezone|None on input; owning form Save contract|searchable IANA zone; do not reinterpret existing reservations|/calendar|
|LIB-01-I01|search-content|None: local UI/navigation; destination resource read only|No payload|/content|
|LIB-01-I02|library-filters|None: local UI/navigation; destination resource read only|No payload|/content|
|LIB-01-I03|sort|None: local UI/navigation; destination resource read only|No payload|/content|
|LIB-01-I04|view-toggle|None: local UI/navigation; destination resource read only|No payload|/content|
|LIB-01-I05|content-open|None: local UI/navigation; destination resource read only|No payload|LIB-02|
|LIB-01-I06|create|None: local UI/navigation; destination resource read only|No payload|CREATE-01|
|LIB-01-I07|content-menu|None: local UI/navigation; destination resource read only|No payload|/content|
|LIB-01-I08|load-more|None: local UI/navigation; destination resource read only|No payload|/content|
|LIB-02-I01|output-open|None: local UI/navigation; destination resource read only|No payload|/content/:contentId|
|LIB-02-I02|content-menu|None: local UI/navigation; destination resource read only|No payload|/content/:contentId|
|LIB-02-I03|duplicate|POST /v1/content/{contentId}/duplicate|{expectedRevision}|LIB-02 with returned new contentId|
|LIB-02-I04|archive-content|POST /v1/content/{contentId}/archive|{expectedRevision}|Remain on /content/:contentId with acknowledged revision/state; no implicit publication or navigation|
|LIB-02-I05|delete-content|POST /v1/content/{contentId}/trash|{expectedRevision}|LIB-01 after successful Trash mutation|
|LIB-02-I06|export-content|POST /v1/content/{contentId}/exports|{outputIds,revision,fileType:zip}|Remain on /content/:contentId with acknowledged revision/state; no implicit publication or navigation|
|LIB-02-I07|activity|None: local UI/navigation; destination resource read only|No payload|ACT-01|
|LIB-02-I08|back|None: local UI/navigation; destination resource read only|No payload|/content/:contentId|
|TRASH-01-I01|restore-content|POST /v1/content/{contentId}/restore|{expectedRevision}|LIB-02 with restored contentId|
|TRASH-01-I02|permanent-delete|DELETE /v1/content/{contentId}/purge|{expectedRevision,confirmationText}|TRASH-01 refreshed after ACK|
|TRASH-01-I03|back|None: local UI/navigation; destination resource read only|No payload|/content/trash|
|ACT-01-I01|activity-tabs|None: local UI/navigation; destination resource read only|No payload|/activity|
|ACT-01-I02|job-filters|None: local UI/navigation; destination resource read only|No payload|/activity|
|ACT-01-I03|job-open|None: local UI/navigation; destination resource read only|No payload|ACT-02|
|ACT-01-I04|retry-job|POST /v1/jobs/{jobId}/retry|{expectedJobRevision,unitId?,correctedConfiguration?}|ACT-02 with returned jobId|
|ACT-01-I05|content-open|None: local UI/navigation; destination resource read only|No payload|LIB-02|
|ACT-01-I06|load-more|None: local UI/navigation; destination resource read only|No payload|/activity|
|ACT-02-I01|job-tabs|None: local UI/navigation; destination resource read only|No payload|/activity/jobs/:jobId|
|ACT-02-I02|diagnostics|POST /v1/diagnostics/exports|{entityId?,includeRedactedLogs:true}|Remain on /activity/jobs/:jobId with acknowledged revision/state; no implicit publication or navigation|
|ACT-02-I03|retry-job|POST /v1/jobs/{jobId}/retry|{expectedJobRevision,unitId?,correctedConfiguration?}|ACT-02 with returned jobId|
|ACT-02-I04|cancel-job|POST /v1/jobs/{jobId}/cancel|{expectedJobRevision,reason}|ACT-02 remains, cancelling/cancelled reported only by server|
|ACT-02-I05|content-open|None: local UI/navigation; destination resource read only|No payload|LIB-02|
|ACT-02-I06|back|None: local UI/navigation; destination resource read only|No payload|/activity/jobs/:jobId|
|NOT-01-I01|notification-open|None: local UI/navigation; destination resource read only|No payload|/notifications|
|NOT-01-I02|mark-read|PATCH /v1/notifications/{notificationId}/read|{read:true}|Remain on /notifications with acknowledged revision/state; no implicit publication or navigation|
|NOT-01-I03|mark-all-read|POST /v1/notifications/read-all|{throughEventId}|Remain on /notifications with acknowledged revision/state; no implicit publication or navigation|
|NOT-01-I04|notification-filter|None on input; owning form Save contract|Unread/All with stable cursor|/notifications|
|NOT-01-I05|notification-settings|None: local UI/navigation; destination resource read only|No payload|SET-08|
|ANA-01-I01|analytics-account|None: local UI/navigation; destination resource read only|No payload|/analytics|
|ANA-01-I02|analytics-date|None on input; owning form Save contract|inclusive local start/end; start<=end; max366days|/analytics|
|ANA-01-I03|analytics-format|None: local UI/navigation; destination resource read only|No payload|/analytics|
|ANA-01-I04|metric-info|None: local UI/navigation; destination resource read only|No payload|/analytics|
|ANA-01-I05|analytics-post|None: local UI/navigation; destination resource read only|No payload|ANA-02|
|ANA-01-I06|compare|None: local UI/navigation; destination resource read only|No payload|ANA-03|
|ANA-01-I07|export-report|POST /v1/analytics/exports|{accountId,range,format,metricIds,postIds,fileType:csv|pdf}|Remain on /analytics with acknowledged revision/state; no implicit publication or navigation|
|ANA-01-I08|refresh-metrics|POST /v1/analytics/refresh|{accountId,range}|Remain on /analytics with acknowledged revision/state; no implicit publication or navigation|
|ANA-02-I01|metric-info|None: local UI/navigation; destination resource read only|No payload|/analytics/posts/:publicationId|
|ANA-02-I02|analytics-date|None on input; owning form Save contract|inclusive local start/end; start<=end; max366days|/analytics/posts/:publicationId|
|ANA-02-I03|view-account|None: local UI/navigation; destination resource read only|No payload|SET-07|
|ANA-02-I04|compare|None: local UI/navigation; destination resource read only|No payload|ANA-03|
|ANA-02-I05|export-report|POST /v1/analytics/exports|{accountId,range,format,metricIds,postIds,fileType:csv|pdf}|Remain on /analytics/posts/:publicationId with acknowledged revision/state; no implicit publication or navigation|
|ANA-02-I06|back|None: local UI/navigation; destination resource read only|No payload|/analytics/posts/:publicationId|
|ANA-03-I01|compare-select|None: local UI/navigation; destination resource read only|No payload|/analytics/compare|
|ANA-03-I02|metric-select|None: local UI/navigation; destination resource read only|No payload|/analytics/compare|
|ANA-03-I03|comparison-period|None on input; owning form Save contract|Calendar date / First7days since publication; age alignment requires sufficient coverage|/analytics/compare|
|ANA-03-I04|export-report|POST /v1/analytics/exports|{accountId,range,format,metricIds,postIds,fileType:csv|pdf}|Remain on /analytics/compare with acknowledged revision/state; no implicit publication or navigation|
|ANA-03-I05|back|None: local UI/navigation; destination resource read only|No payload|/analytics/compare|
|SET-01-I01|settings-destination|None: local UI/navigation; destination resource read only|No payload|/settings|
|SET-02-I01|profile-name|None on input; owning form Save contract|1–80characters; trimmed|/settings/profile|
|SET-02-I02|avatar|None on input; owning form Save contract|JPEG/PNG<=5MiB; square crop; EXIF removed|/settings/profile|
|SET-02-I03|language|None on input; owning form Save contract|English initial release; other choices disabled with explanation|/settings/profile|
|SET-02-I04|timezone|None on input; owning form Save contract|searchable IANA zone; do not reinterpret existing reservations|/settings/profile|
|SET-02-I05|save-settings|None: local UI/navigation; destination resource read only|No payload|/settings/profile|
|SET-03-I01|research-toggle|None on input; owning form Save contract|off default; saving activates next run, not immediate run|/settings/research|
|SET-03-I02|research-time|None on input; owning form Save contract|HH:mm local; default08:00|/settings/research|
|SET-03-I03|timezone|None on input; owning form Save contract|searchable IANA zone; do not reinterpret existing reservations|/settings/research|
|SET-03-I04|category-mix|None on input; owning form Save contract|one or more supported categories|/settings/research|
|SET-03-I05|auto-draft|None on input; owning form Save contract|off default; enables paid draft generation only with explicit saved configuration; never publish|/settings/research|
|SET-03-I06|save-settings|None: local UI/navigation; destination resource read only|No payload|/settings/research|
|SET-03-I07|run-research|POST /v1/research/runs|{window:last_24_hours,categoryIds,rankingPolicyRevision,sourceCatalogRevision}|ACT-02 job detail; DISC-01?run=:runId for findings|
|SET-04-I01|provider-open|None: local UI/navigation; destination resource read only|No payload|SET-05|
|SET-04-I02|connect-provider|None: local UI/navigation; destination resource read only|No payload|SET-05|
|SET-04-I03|test-provider|POST /v1/providers/{providerId}/test|{candidateCredential?,modelIds}|Remain on /settings/providers with acknowledged revision/state; no implicit publication or navigation|
|SET-04-I04|disconnect-provider|DELETE /v1/providers/{providerId}/connection|{expectedRevision,confirmed:true}|Remain on /settings/providers with acknowledged revision/state; no implicit publication or navigation|
|SET-05-I01|provider-key|None on input; owning form Save contract|write-only secure entry; never shown after save|/settings/providers/:providerId|
|SET-05-I02|provider-model|None on input; owning form Save contract|capability-supported ID only|/settings/providers/:providerId|
|SET-05-I03|test-provider|POST /v1/providers/{providerId}/test|{candidateCredential?,modelIds}|Remain on /settings/providers/:providerId with acknowledged revision/state; no implicit publication or navigation|
|SET-05-I04|save-provider|PUT /v1/providers/{providerId}/credentials|{candidateCredential,modelIds,expectedRevision}|Remain on /settings/providers/:providerId with acknowledged revision/state; no implicit publication or navigation|
|SET-05-I05|disconnect-provider|DELETE /v1/providers/{providerId}/connection|{expectedRevision,confirmed:true}|Remain on /settings/providers/:providerId with acknowledged revision/state; no implicit publication or navigation|
|SET-05-I06|back|None: local UI/navigation; destination resource read only|No payload|/settings/providers/:providerId|
|SET-06-I01|connect-instagram|POST /v1/instagram/oauth/start|{returnTo}|Remain on /settings/instagram with acknowledged revision/state; no implicit publication or navigation|
|SET-06-I02|account-open|None: local UI/navigation; destination resource read only|No payload|SET-07|
|SET-06-I03|test-instagram|POST /v1/instagram/{accountId}/test|{}|Remain on /settings/instagram with acknowledged revision/state; no implicit publication or navigation|
|SET-06-I04|reconnect-instagram|POST /v1/instagram/{accountId}/reconnect|{returnTo}|Remain on /settings/instagram with acknowledged revision/state; no implicit publication or navigation|
|SET-06-I05|disconnect-instagram|DELETE /v1/instagram/{accountId}|{expectedRevision,confirmed:true}|Remain on /settings/instagram with acknowledged revision/state; no implicit publication or navigation|
|SET-07-I01|test-instagram|POST /v1/instagram/{accountId}/test|{}|Remain on /settings/instagram/:accountId with acknowledged revision/state; no implicit publication or navigation|
|SET-07-I02|reconnect-instagram|POST /v1/instagram/{accountId}/reconnect|{returnTo}|Remain on /settings/instagram/:accountId with acknowledged revision/state; no implicit publication or navigation|
|SET-07-I03|disconnect-instagram|DELETE /v1/instagram/{accountId}|{expectedRevision,confirmed:true}|Remain on /settings/instagram/:accountId with acknowledged revision/state; no implicit publication or navigation|
|SET-07-I04|blocked-schedules|None: local UI/navigation; destination resource read only|No payload|CAL-01|
|SET-07-I05|back|None: local UI/navigation; destination resource read only|No payload|/settings/instagram/:accountId|
|SET-08-I01|notification-toggle|None on input; owning form Save contract|job/review/publication per channel boolean|/settings/notifications|
|SET-08-I02|enable-push|None: local UI/navigation; destination resource read only|No payload|/settings/notifications|
|SET-08-I03|quiet-hours|None on input; owning form Save contract|start/end local; timezone explicit; publication failures bypass quiet-hour delay|/settings/notifications|
|SET-08-I04|open-os-settings|None: local UI/navigation; destination resource read only|No payload|/settings/notifications|
|SET-08-I05|save-settings|None: local UI/navigation; destination resource read only|No payload|/settings/notifications|
|SET-09-I01|session-revoke|DELETE /v1/sessions/{sessionId}|{recentAuthProof}|Remain on /settings/security with acknowledged revision/state; no implicit publication or navigation|
|SET-09-I02|link-apple|POST /v1/me/apple|{identityToken,nonce,recentAuthProof}|Remain on /settings/security with acknowledged revision/state; no implicit publication or navigation|
|SET-09-I03|sign-out|POST /v1/auth/logout|{allDevices:boolean}|AUTH-01 after protected buffer decision and server session revocation|
|SET-09-I04|sign-out-all|POST /v1/auth/logout|{allDevices:boolean}|AUTH-01 after session revocation|
|SET-10-I01|workspace-name|None on input; owning form Save contract|1–80characters; trimmed|/settings/workspace|
|SET-10-I02|member-role|PATCH /v1/workspaces/{workspaceId}/members/{memberId}|{expectedRevision,role,publishPermission}|Remain on /settings/workspace with acknowledged revision/state; no implicit publication or navigation|
|SET-10-I03|invite-member|POST /v1/workspaces/{workspaceId}/invitations|{email,role,publishPermission:false}|Remain on /settings/workspace with acknowledged revision/state; no implicit publication or navigation|
|SET-10-I04|remove-member|DELETE /v1/workspaces/{workspaceId}/members/{memberId}|{expectedRevision,confirmed:true}|Remain on /settings/workspace with acknowledged revision/state; no implicit publication or navigation|
|SET-10-I05|save-settings|None: local UI/navigation; destination resource read only|No payload|/settings/workspace|
|SET-11-I01|export-data|POST /v1/data/exports|{recentAuthProof}|Remain on /settings/data with acknowledged revision/state; no implicit publication or navigation|
|SET-11-I02|delete-account|POST /v1/account/deletion|{recentAuthProof,confirmedRetention:true}|Remain on /settings/data with acknowledged revision/state; no implicit publication or navigation|
|SET-11-I03|privacy|None: local UI/navigation; destination resource read only|No payload|SET-11|
|SET-11-I04|help|None: local UI/navigation; destination resource read only|No payload|HELP-01|
|HELP-01-I01|help-search|None: local UI/navigation; destination resource read only|No payload|/help|
|HELP-01-I02|help-article|None: local UI/navigation; destination resource read only|No payload|/help|
|HELP-01-I03|export-diagnostics|POST /v1/diagnostics/exports|{entityId?,includeRedactedLogs:true}|Remain on /help with acknowledged revision/state; no implicit publication or navigation|
|HELP-01-I04|back|None: local UI/navigation; destination resource read only|No payload|/help|
|SYS-01-I01|sign-in|None: local UI/navigation; destination resource read only|No payload|AUTH-01|
|SYS-01-I02|switch-workspace|None: local UI/navigation; destination resource read only|No payload|/session-recovery|
|SYS-01-I03|export-local-draft|None: local UI/navigation; destination resource read only|No payload|/session-recovery|
|SYS-02-I01|back|None: local UI/navigation; destination resource read only|No payload|/not-found|
|SYS-02-I02|home|None: local UI/navigation; destination resource read only|No payload|HOME-01|
|GEN-02-I01|view-job|None: local UI/navigation; destination resource read only|No payload|ACT-02|
|GEN-02-I02|retry-unit|POST /v1/jobs/{jobId}/retry|{expectedJobRevision,unitId?,correctedConfiguration?}|Remain on /content/:contentId/reel/generation with acknowledged revision/state; no implicit publication or navigation|
|GEN-02-I03|cancel-generation|POST /v1/jobs/{jobId}/cancel|{expectedJobRevision,reason}|Current generation screen remains with cancelling then retained partial assets|
|GEN-02-I04|open-editor|None: local UI/navigation; destination resource read only|No payload|/content/:contentId/reel/generation|
|GEN-02-I05|library|None: local UI/navigation; destination resource read only|No payload|LIB-01|
|REEL-05-I10|generate-voiceover|POST /v1/outputs/{outputId}/voiceover|Expected revision, input hashes and explicit confirmation; contract-addenda.md|/content/:contentId/reel/audio|
|REEL-06-I07|generate-subtitles|POST /v1/outputs/{outputId}/subtitles|Expected revision, input hashes and explicit confirmation; contract-addenda.md|/content/:contentId/reel/subtitles|
|PUB-02-I06|resume-publication|POST /v1/publications/{publicationId}/resume|Expected revision, input hashes and explicit confirmation; contract-addenda.md|/publications/:publicationId|
|SET-11-I05|cancel-deletion|DELETE /v1/account/deletion|Expected revision, input hashes and explicit confirmation; contract-addenda.md|/settings/data|
|IMPORT-01-I09|submission-mode|None: local radio|contract-addenda.md URL-only intake|/topics/new?idea=:ideaId|
|IMPORT-01-I10|extract-url|POST /v1/ideas|contract-addenda.md URL-only intake|/topics/new?idea=:ideaId|
|IMPORT-01-I11|confirm-excerpt|POST /v1/ideas/{ideaId}/confirm|contract-addenda.md URL-only intake|TOPIC-01 with returned topicId|
|IMPORT-01-I12|cancel-extraction|POST /v1/jobs/{jobId}/cancel|contract-addenda.md URL-only intake|/topics/new?idea=:ideaId|
|CREATE-02-AI11|inspect-creative-plan|GET /v1/outputs/{outputId}/creative-plan|ai-creative-autopilot.md|/create/:setupId/configure|
|CAR-01-AI13|different-look|POST /v1/outputs/{outputId}/different-look|ai-creative-autopilot.md|/content/:contentId/carousel|
|CAR-01-AI14|view-comparison|GET /v1/outputs/{outputId}/creative-plan|ai-creative-autopilot.md|/content/:contentId/carousel|
|REEL-01-AI17|different-look|POST /v1/outputs/{outputId}/different-look|ai-creative-autopilot.md|/content/:contentId/reel|
|REEL-01-AI18|view-comparison|GET /v1/outputs/{outputId}/creative-plan|ai-creative-autopilot.md|/content/:contentId/reel|
|CAR-03-AI3|inspect-creative-plan|GET /v1/outputs/{outputId}/creative-plan|ai-creative-autopilot.md|/content/:contentId/carousel/regenerate/:slideId|
|GEN-01-EX7|different-look|POST /v1/outputs/{outputId}/different-look|AI creative autopilot contract or selected topic/setupID|/content/:contentId/generation|
|GEN-01-EX8|view-comparison|GET /v1/outputs/{outputId}/creative-plan|AI creative autopilot contract or selected topic/setupID|/content/:contentId/generation|
|GEN-02-EX6|different-look|POST /v1/outputs/{outputId}/different-look|AI creative autopilot contract or selected topic/setupID|/content/:contentId/reel/generation|
|GEN-02-EX7|view-comparison|GET /v1/outputs/{outputId}/creative-plan|AI creative autopilot contract or selected topic/setupID|/content/:contentId/reel/generation|
|CREATE-01-EX6|optional-preferences|None: navigation|AI creative autopilot contract or selected topic/setupID|/create?topic=:topicId|
|CREATE-01-EX7|choose-topic|GET /v1/topics?q=&cursor=|AI creative autopilot contract or selected topic/setupID|/create?topic=:topicId|
|CREATE-01-EX8|custom-topic|None: navigation|AI creative autopilot contract or selected topic/setupID|/create?topic=:topicId|
|REVIEW-02-EX9|acknowledge-style-warning|POST /v1/outputs/{outputId}/diversity/acknowledge|AI creative autopilot contract or selected topic/setupID|/review/:contentId/:format|
|DISC-01-R24-research-history|research-history|None: navigation|product-scope-v3.md fixed-run contract|DISC-02|
|DISC-01-R24-ranking-explanation|ranking-explanation|GET /v1/findings/{findingId}|product-scope-v3.md fixed-run contract|Ranking sheet; close to selected finding|
|DISC-01-R24-show-all-findings|show-all-findings|GET /v1/research/runs/{runId}/findings|product-scope-v3.md fixed-run contract|DISC-01?run=:runId&disposition=all|
|DISC-01-R24-duplicate-group|duplicate-group|GET /v1/research/runs/{runId}/findings?duplicateGroupId=|product-scope-v3.md fixed-run contract|Duplicate-group detail sheet|
|DISC-02-R24-run-open|run-open|GET /v1/research/runs/{runId}/findings|product-scope-v3.md fixed-run contract|DISC-01?run=:runId|
|DISC-02-R24-coverage-details|coverage-details|GET /v1/research/runs/{runId}|product-scope-v3.md fixed-run contract|Coverage sheet|
|DISC-02-R24-retry-sources|retry-sources|POST /v1/research/runs/{runId}/retry-sources|product-scope-v3.md fixed-run contract|ACT-02 returnedjobId|
|DISC-02-R24-history-filters|history-filters|GET /v1/research/runs?status=&from=&to=&cursor=|product-scope-v3.md fixed-run contract|DISC-02|
|DISC-02-R24-load-more|load-more|GET /v1/research/runs?cursor=|product-scope-v3.md fixed-run contract|DISC-02|
|DISC-02-R24-back|back|None: navigation|product-scope-v3.md fixed-run contract|DISC-01|
