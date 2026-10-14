# Sinopia

Sinopia is a workload-monitoring prototype for coaches of youth sports teams. It records session duration and perceived effort, plus optional athlete self-reported wellness check-ins. The output is a prompt for a coach conversation. It is not a medical device, does not diagnose injuries, and uses provisional thresholds that have not been validated against season outcomes.

Do not collect real athlete information until production authentication, hosting configuration, retention, encryption, privacy review, and migration work have been completed and verified.

## Local setup

Use Python 3.12 and Node.js 20 or a compatible supported release.

Install backend dependencies from the repository root.

```bash
python -m pip install -r requirements.txt
$env:SINOPIA_ENV = "development"
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

The backend command above explicitly opts into local development mode. Set the frontend and landing environment variables from their example files as needed. Local development uses a development coach and must never be exposed as a public service. Production defaults to fail-closed mode and requires HTTPS origins, Google configuration, and the encryption key ring.

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

GitHub Actions runs the backend test suite, dependency audits, secret scan, and both Vite builds for pull requests targeting main. It can also be run manually. Pushes to the working security branch do not trigger a second redundant CI run.

## Security behaviour in this branch

Coach routes require a coach session and are scoped to the owning team. Google ID tokens are verified server-side, and the backend issues an opaque server-side session in an HttpOnly cookie. Production deployment must set SINOPIA_ENV=production, configure GOOGLE_CLIENT_ID and VITE_GOOGLE_CLIENT_ID, and set SINOPIA_ALLOWED_ORIGINS to exact trusted origins.

Athlete check-in links use a separate random token, not the athlete's player ID. The token is placed in the URL fragment, so it is not sent in HTTP requests or normal server access logs. A coach can regenerate a token to invalidate an older link. The API allows one check-in per athlete per day. A pain flag remains active until a coach acknowledges it. Coach exports are team-scoped, and account deletion requires a fresh Google ID token.

The current rate throttles are process-local. They are not a substitute for shared rate limiting in a multi-worker deployment. Athlete labels and pain-area values use application-level AES-GCM encryption when a key ring is configured; production refuses to start without it. Automated retention enforcement is not implemented. The current store is SQLite; PostgreSQL migration and a controlled migration of legacy records remain outstanding. Do not deploy with sensitive athlete data until these gaps are closed.

## Configuration

The backend environment variables are listed in .env.example. The frontend and landing environment examples document the API URL, Google sign-in client ID, legal page URL, coach app URL, and privacy contact setting. Do not commit secrets or real credentials.

## Privacy and operational documents

The public privacy notice, terms, and deletion information are available from the landing application at /privacy, /terms, and /delete-account. These are drafts that require qualified legal review and completion of all placeholders before launch.

Operational drafts are in docs/data-map.md, docs/dpia.md, docs/breach-response.md, and docs/play-store-checklist.md. The security.txt template under .well-known must be completed with a monitored contact and canonical public URL before release.

## Known gaps before production

The Vercel first-party /api rewrite and exact production CSP still need the actual deployed backend hostname. The current branch does not yet implement scheduled 12-month retention, inactive-account warnings, a PostgreSQL migration, or a configured first-party /api rewrite. Those require a migration plan, scheduler/notification decision, and the actual deployed backend hostname. Confirm actual subprocessors and processing regions, test deletion across backups, and complete an independent security and privacy review before collecting real athlete data.


## Application-level encryption

In production, Sinopia refuses to start without SINOPIA_ENCRYPTION_KEYS. Configure a comma-separated key ring in the host secret manager, with the active key first and any older decryption keys after it. Each value must be a unique key ID followed by a colon and a base64url-encoded 32-byte key. Generate a key locally with Python using secrets.token_bytes(32) and base64.urlsafe_b64encode; never commit it. Athlete labels and pain-area values are encrypted using AES-GCM. Startup migration re-encrypts legacy plaintext values and rotates values encrypted with older configured keys. Keep old keys available until migration has completed successfully and backups encrypted with those keys have expired. The label lookup digest is keyed by the active key and is rebuilt on startup during key rotation. This implementation still uses SQLite; PostgreSQL migration remains outstanding.


## Hosting and user feedback

Use [the launch checklist](docs/launch-checklist.md) to configure the backend, the coach frontend, and the landing/legal site. The coach frontend includes a same-origin Vercel Edge proxy at `/api/*`; configure the server-side `SINOPIA_BACKEND_URL` environment variable in Vercel and allow the exact coach frontend origin in the backend. The frontend project must set `VITE_API_BASE=/api`, the Google client ID, and the landing-site legal URL. The landing project must set the deployed coach URL and a monitored contact address. These deployment values are deliberately not guessed or committed.

The current branch is suitable for preparing a synthetic-data alpha only after its actual hosting configuration has been verified. A short, privacy-preserving tester script is included in `docs/launch-checklist.md`. It is not cleared for real athlete or child health data while SQLite, automated retention, shared rate limiting, and the remaining privacy/security operational controls are outstanding.
