# Sinopia

Sinopia is a workload-monitoring tool for youth-team coaches. Its outputs are prompts for coach conversations, not diagnoses or injury predictions.

## Vercel projects and environment variables

Configure these separately for each Vercel project. Never commit real secrets.

### API (FastAPI entrypoint: `backend.main:app`)
- `DATABASE_URL` — Neon pooled PostgreSQL connection string. Use the pooled hostname, username/password/database from Neon, and `sslmode=require`. Mark **Sensitive**.
- `CORS_ORIGINS` — comma-separated exact origins permitted to call the API, including the deployed coach app and landing page. Not secret.
- Google/session variables are required before enabling coach authentication: `GOOGLE_CLIENT_ID`, `SESSION_SECRET`, and `SESSION_COOKIE_SECURE`. Mark `SESSION_SECRET` **Sensitive**. Do not deploy authentication until its server-side verification is implemented and tested.

### Coach app (`frontend`)
- `VITE_API_BASE` — normally `/api` when the configured Vercel rewrite points to the API deployment. Not secret.
- `VITE_GOOGLE_CLIENT_ID` — Google OAuth web client ID. Public configuration, not a secret.
- `VITE_LEGAL_BASE_URL` — optional URL for the public privacy/terms pages. Not secret.

### Landing page (`landing`)
- `VITE_COACH_APP_URL` — origin of the deployed coach app, e.g. `https://sinopia-app.vercel.app`. Not secret.
- `VITE_CONTACT_EMAIL` — optional public contact address. Not secret.

### Local development and tests
- `DATABASE_URL` — can be set to `sqlite:///./sinopia-test.db` for local development, or to a disposable SQLite URL in tests. Production must use Neon.
- Never use a production database for automated tests.

## Deployment notes
The API creates SQLAlchemy tables at startup. Set environment variables before deploying. Check Vercel function logs for server-side failures; responses intentionally avoid logging or returning athlete information.
