# DevAI Studio

Developer-news discovery, AI-assisted Instagram carousel drafting, editable 1080 × 1350 images, human review, and approval-gated publishing.

**Status:** Development build. Do not deploy publicly; browser-shipped API keys are insecure. Live Meta publishing, production authentication, durable scheduling, image hosting, and complete end-to-end tests are not yet verified.

## Local setup

1. Install Docker Desktop.
2. Copy your secrets to a local `.env` file (never commit it).
3. Run `docker compose up --build`.
4. Visit `http://localhost:5173`. API docs: `http://localhost:8000/docs`.
5. For iOS, in `mobile`, run `npm install` and `npm start`; configure `EXPO_PUBLIC_API_URL` with your computer's LAN address and enter the development API key.

## Testing

```bash
cd api
pip install -r requirements.txt pytest
pytest -q
```

## Components

- `api/main.py`: FastAPI routes, SQLAlchemy models, approval state machine, PNG export, publishing reservation.
- `api/research.py`: RSS news discovery and clearly marked editorial scaffolds.
- `api/generation.py`: source-grounded LLM drafts; requires `OPENAI_API_KEY`.
- `api/daily.py`, `api/scheduler.py`: daily discovery and duplicate URL checks.
- `api/instagram.py`: Meta Graph API carousel adapter; requires `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_ACCOUNT_ID`, and publicly hosted image URLs.
- `web/`: React/Vite content dashboard.
- `mobile/`: Expo React Native review application.

## Safety

Content must be explicitly submitted and approved before publishing. Editing invalidates approval. Publishing failures require manual reconciliation; do not blindly retry. Daily discovery only creates drafts and does not auto-publish. Do not commit secrets.
