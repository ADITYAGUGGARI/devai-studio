# Revision 4 implementation environment

Revision 4 is still being implemented. The current verified subsets are recorded in `IMPLEMENTATION_STATUS.md`; the screen checklist is `ux/V4_IMPLEMENTATION_COVERAGE.csv`. This document does not certify all A–O workflows.

The implementation worktree is `/Users/aditya/Desktop/local/devai-studio-ux-v4`, branch `feat/devai-studio-ux-v4`. The original worktree and database were preserved. The preview uses a separate database named `devai_v4_local`, backend port8125 and web port5185.

## Dependencies and migrations

Use Python3.12+, Node22 and Docker Desktop. Create a local `.env` from `.env.example`; configure server values there. Install dependencies using the repository setup instructions, including `npm ci`, `npm --prefix web ci`, `npm --prefix mobile ci` and the editable API development package.

Start PostgreSQL with `docker compose up -d postgres`. Existing Compose configuration requires a nonempty `ADMIN_PASSWORD` during configuration parsing, even when starting only PostgreSQL. For the isolated preview, create `devai_v4_local` once:

```sh
docker compose exec -T postgres psql -U devai -d postgres -c 'CREATE DATABASE devai_v4_local'
```

Set `DATABASE_URL=postgresql+psycopg://devai:devai_local_only@127.0.0.1:5433/devai_v4_local`. Apply migrations explicitly:

```sh
PYTHONPATH=api/src .venv/bin/python -m devai.migrate upgrade head
```

Migration0002 adopts existing content into the original studio and adds isolation, version history and research snapshots. Migration0003 adds email authentication challenges. Back up existing databases before applying migrations; use the existing backup/restore documentation. The downgrade of workspace isolation refuses to collapse multiple studios.

## Preview startup

With server environment values loaded, run:

```sh
CORS_ORIGINS=http://127.0.0.1:5185,http://127.0.0.1:5187 PYTHONPATH=api/src .venv/bin/python -m uvicorn devai.main:app --host 127.0.0.1 --port 8125
VITE_API_URL=http://127.0.0.1:8125 npm --prefix web run dev -- --port 5185 --strictPort
EXPO_PUBLIC_API_URL=http://127.0.0.1:8125 npm --prefix mobile start
```

Web: `http://127.0.0.1:5185`; Swagger: `http://127.0.0.1:8125/docs`. The iOS simulator can use loopback; a physical device needs the Mac's reachable private address and suitable development networking. No public deployment is required for local review.

The API processes durable jobs when `BACKGROUND_WORKER_ENABLED=true`. For separate workers, set it false in the API and start `make worker` with the same database/provider environment. Start `make scheduler` with the same database configuration: it now checks per-workspace revision4 research schedules as well as the preserved legacy daily workflow. Revision4 schedules default off. Configure them at `/settings/research` or the native Settings → Research schedule screen. Saving enables the next future daily run; it does not start a past time immediately. Daily reservations survive restarts, use each studio's timezone, choose the first fall-back occurrence and the next valid spring-forward time, and retain a frozen previous24hourwindow and category choices. Automatic revision4 drafting remains unavailable; no schedule publishes content.

The currently running preview was explicitly started in development API-key mode on loopback. Normal account verification should use `ALLOW_DEV_API_KEY=false` and server bootstrap credentials or configured email sign-in. Development keys are visible to clients and are not provider credentials.

## Email and provider configuration

Email sign-in requires server-only `APP_SECRET` with at least32characters, `SMTP_HOST`, `SMTP_FROM`, optional `SMTP_USERNAME`/`SMTP_PASSWORD`, `SMTP_PORT` and `SMTP_TLS_MODE=starttls` or `ssl`. Transport verifies TLS certificates. Codes expire after10minutes; resend is limited, five wrong verification attempts exhaust a challenge, and code hashes are persisted. Missing delivery configuration produces an actionable unavailable state. No code is printed or returned to the UI. Password sign-in remains available for existing accounts. Apple sign-in and session refresh remain implementation work.

AI generation retains the existing `OPENAI_API_KEY` and model configuration. Real speech uses `OPENAI_SPEECH_MODEL` (default `gpt-4o-mini-tts`). See the official [speech API guide](https://developers.openai.com/api/docs/guides/text-to-speech). Voiceover is not replaced with silence on failure.

The backend container installs FFmpeg. Native local rendering needs `ffmpeg`/`ffprobe` on PATH or explicit `FFMPEG_BIN`/`FFPROBE_BIN`. Linux uses `libx264`; macOS uses `h264_videotoolbox`; `REEL_VIDEO_ENCODER` overrides the selection. Local verification compiled official FFmpeg8.0 into `/private/tmp/devai-ffmpeg`; this temporary dependency is not bundled or committed. Persisted Reel orchestration and web/native editors now use these codecs. Burned subtitles require libass; the Docker worker includes it, while the temporary Mac build does not. See `CONTENT_OUTPUTS.md` for setup, media persistence, budgets and accurate verification limits.

Instagram retains its existing server configuration requirements: access token, account ID and publicly accessible approved media origin. Revision4 multi-account OAuth/publication contracts remain incomplete, and current Meta requirements still need official verification. Local tests never publish real Instagram content.

## Verification commands

```sh
npm run check
PYTHONPATH=api/src .venv/bin/python -m pytest -c api/pyproject.toml api/tests -q
PLAYWRIGHT_CHROMIUM_CHANNEL=chrome npm run test:e2e
PLAYWRIGHT_CHROMIUM_CHANNEL=chrome npx playwright test -c playwright.v4.config.ts
```

The dedicated v4 browser check requires the isolated preview above; other browser tests use isolated fixtures. PostgreSQL tests create disposable schemas when `TEST_DATABASE_URL` is set. Codec integration needs FFmpeg configured; without it the actual-render test is explicitly skipped. iOS TypeScript is checked by `npm run check`; native simulator/VoiceOver/DynamicType acceptance remains separate.

Revision4 personal preferences use migration0004 (`user_profiles`) and `/v1/me`. These routes require a real signed-in personal account; the development API header has no personal identity. Email delivery requires the SMTP settings below, or configure the preserved bootstrap local account before first startup. There is no default personal password. Profile changes do not reinterpret any stored publication reservation.

Native acceptance can use `PYTHONPATH=api/src .venv/bin/python scripts/e2e_server.py` (isolated PostgreSQL schema/API8124) and `EXPO_PUBLIC_API_URL=http://127.0.0.1:8124 npm --prefix mobile start -- --localhost --port 8086`. With the installed ExpoGo54 container, run `MAESTRO_CLI_NO_ANALYTICS=1 maestro --device <simulator-id> test mobile/.maestro/v4-profile-expo.yaml` or `mobile/.maestro/v4-research-schedule-expo.yaml`. These use explicit test-only credentials; they are separate from previewAPI8125 and normal Metro8085. Profile and schedule save/back/Stay/Discard subsets have passed on the iPhone simulator; complete native acceptance remains outstanding. Do not run connected Playwright and the native acceptance API on8124 simultaneously.

Authenticated review preview: start Vite with `VITE_API_URL=http://127.0.0.1:8125 VITE_DEV_API_KEY_ENABLED=false npm --prefix web run dev -- --port 5187 --strictPort`. The backend must allow both preview origins, as shown above; missing5187 causes browser sign-in to fail despite a valid account. Personal accounts are provisioned with the existing administrator account endpoint or bootstrap configuration; no password is stored in this documentation. The actual review-origin browser test reads `LOCAL_REVIEW_EMAIL` and `LOCAL_REVIEW_PASSWORD` from its environment.
