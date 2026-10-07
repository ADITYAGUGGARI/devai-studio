# Product feature status

## Implemented

- Existing React dashboard shell, library, editor, manual drafts and review transitions, extended with a prioritized persistent topic queue, category filtering, selection of 6–8 slides and progress controls.
- Daily official-source research, canonical URL/title deduplication, retained evidence/dates/citations, editorial rotation, manual-source human verification and priority/archive controls.
- Original grounded copy, independent claim/evidence audit, recent-angle and full-copy similarity checks.
- Individual complete AI image compositions including typography; dimension checks, vision transcription comparison, legibility/clipping checks, duplicate detection, two-pass validation repair, and single-slide regeneration.
- Persistent database-backed jobs, leases/heartbeats, progress polling, retries with backoff, recovery and reuse of validated slides. API background worker, standalone worker and scheduler commands.
- Review/approval with source and image checks, invalidation on edits, version/content/image hashes, and PNG ZIP export with caption, sources and review metadata.
- Approval-gated Instagram publishing jobs using immutable managed JPEG snapshots, public tokenized media URLs, version reservation, uncertainty handling and human reconciliation.
- Additive compatibility schema updates for existing local installations; existing data and assets retained. New tables are created at startup.

## External configuration or verification required

- OpenAI API key, billing and model access for copy, grounding, images and vision checks. AI validation is fallible; human review is mandatory.
- Enable `DAILY_ENABLED=true` or run `make scheduler`, and keep a worker running. A code/configured schedule does not establish an active daily service.
- Instagram professional-account publishing token, account ID, supported Graph version and app permissions, plus a publicly reachable HTTPS API media origin. Live publishing is not verified by fake-adapter tests.
- Review real generated image lettering, visual continuity and readability on phones. Originality checks do not inspect all public Instagram posts.
- Public deployment: account authentication/authorization, backups, monitoring, versioned production migration tooling and asset retention/cleanup.
- Native iOS/Android walkthrough and inherited Expo dependency upgrade remain outstanding.

See [workflow and operations](workflow.md) for endpoints, configuration, retry/recovery behavior and publishing setup.
