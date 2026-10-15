# Sinopia

Sinopia is a workload-monitoring tool for youth-team coaches. Its outputs are prompts for coach conversations, not diagnoses or injury predictions.

## Vercel projects and environment variables

Configure these separately for each Vercel project. Never commit real secrets.

### API (FastAPI entrypoint: `backend.main:app`)
- `DATABASE_URL` — Neon pooled PostgreSQL connection string. Use the pooled hostname, username/password/database from Neon, and `sslmode=require`. Mark **Sensitive**.
- `CORS_ORIGINS` — comma-separated exact origins permitted to call the API, including the deployed coach app and landing page. Not secret.
- Google/session variables: `GOOGLE_CLIENT_ID` (same OAuth client as the frontend), `SESSION_SECRET` (strong random value; mark **Sensitive**), and `SESSION_COOKIE_SECURE=true` in production. Google ID tokens are verified by the API and the app uses a signed HttpOnly session cookie.

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

## Core flows
- Coaches sign in with Google, confirm age/authorization declarations at sign-up, accept the terms, and create one team with a saved composition.
- Athlete check-in links use separate opaque tokens and do not require an account. The public check-in response omits internal player/team IDs.
- When a coach opens a team session, the athlete check-in asks for effort (0–10) and records session load; closing the session removes that question from newly opened links.

## Deployment notes
The API creates SQLAlchemy tables at startup and migrates the original player table to team-scoped IDs. Set environment variables before deploying. `frontend/vercel.json` contains the current API deployment destination; update it if the API Vercel hostname changes. Check Vercel function logs for server-side failures; responses intentionally avoid returning athlete information.
