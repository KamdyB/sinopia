# Sinopia

Sinopia is a workload-monitoring prototype for coaches of youth sports teams. It records session duration and perceived effort, plus optional athlete self-reported wellness check-ins. The output is a prompt for a coach conversation. It is not a medical device, does not diagnose injuries, and uses provisional thresholds that have not been validated against season outcomes.

Do not collect real athlete information until production authentication, hosting configuration, retention, encryption, privacy review, and migration work have been completed and verified.

## Local setup

Use Python 3.12 and Node.js 20 or a compatible supported release.

Install backend dependencies from the repository root.

```bash
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

In a second terminal, start the coach app.

```bash
cd frontend
npm install
npm run dev
```

Start the public landing and legal pages in another terminal.

```bash
cd landing
npm install
npm run dev
```

Copy the example environment files to local environment files and configure the Google client ID if testing the production sign-in path. Local development uses a development coach and must never be exposed as a public service.

## Tests and builds

Run backend tests from the repository root.

```bash
python -m pytest -q
```

Build the coach app and landing page separately.

```bash
cd frontend && npm run build
cd ../landing && npm run build
```

GitHub Actions runs the backend test suite and both Vite builds on pushes to the security branch and on pull requests.

## Security behaviour in this branch

Coach routes require a coach session and are scoped to the owning team. Google ID tokens are verified server-side, and the backend issues an opaque server-side session in an HttpOnly cookie. Production deployment must set SINOPIA_ENV=production, configure GOOGLE_CLIENT_ID and VITE_GOOGLE_CLIENT_ID, and set SINOPIA_ALLOWED_ORIGINS to exact trusted origins.

Athlete check-in links use a separate random token, not the athlete's player ID. A coach can regenerate a token to invalidate an older link. The API allows one check-in per athlete per day. A pain flag remains active until a coach acknowledges it. Coach exports are team-scoped, and account deletion requires a fresh Google ID token.

The current IP throttles are process-local. They are not a substitute for shared rate limiting in a multi-worker deployment. Application-level encryption and automated retention enforcement are not implemented. The current store is SQLite; PostgreSQL migration and a controlled migration of legacy records remain outstanding. Do not deploy with sensitive athlete data until these gaps are closed.

## Configuration

The backend environment variables are listed in .env.example. The frontend and landing environment examples document the API URL, Google sign-in client ID, legal page URL, coach app URL, and privacy contact setting. Do not commit secrets or real credentials.

## Privacy and operational documents

The public privacy notice, terms, and deletion information are available from the landing application at /privacy, /terms, and /delete-account. These are drafts that require qualified legal review and completion of all placeholders before launch.

Operational drafts are in docs/data-map.md, docs/dpia.md, docs/breach-response.md, and docs/play-store-checklist.md. The security.txt template under .well-known must be completed with a monitored contact and canonical public URL before release.

## Known gaps before production

The Vercel first-party /api rewrite and exact production CSP still need the actual deployed backend hostname. The current branch does not yet implement application-level encryption, scheduled 12-month retention, inactive-account warnings, or a PostgreSQL migration. Confirm actual subprocessors and processing regions, test deletion across backups, and complete an independent security and privacy review before collecting real athlete data.
