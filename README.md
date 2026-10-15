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


Athlete check-in links use a separate random token, not the athlete's player ID. The token is placed in the URL fragment, so it is not sent in HTTP requests or normal server access logs. A coach can regenerate a token to invalidate an older link. The API allows one check-in per athlete per day. When a coach opens a team session, the athlete check-in also asks for effort on a 0–10 scale and records duration × effort in workload history; closing the session removes the prompt from newly opened links. A pain flag remains active until a coach acknowledges it. Coach exports are team-scoped, and account deletion requires a fresh Google ID token.

Production rate-limit counters are stored in PostgreSQL so they are shared across function instances. Production API requests also require a server-only shared secret from the first-party Vercel proxy; a Cloudflare edge rule and production proxy/IP verification still need deployment testing. Athlete labels and pain-area values use application-level AES-GCM encryption when a key ring is configured; production refuses to start without it. Automated retention is configurable through the daily Vercel cron. It fails closed and deletes nothing until `CRON_SECRET` and an explicitly approved `SINOPIA_RETENTION_DAYS` value are configured. The security branch adds a SQLAlchemy PostgreSQL adapter and an owner-role schema/RLS migration command. CI tests RLS with a restricted non-owner role. Existing SQLite records are not automatically copied to PostgreSQL; any legacy data migration must be separately tested. Do not deploy with sensitive athlete data until these gaps are closed.

## Vercel environment variables

Set these per project in Vercel. Do not put secrets in any `VITE_*` variable.

### API project (repository root; `backend.main:app`)
- `SINOPIA_ENV=production` — not secret.
- `DATABASE_URL` — Neon pooled PostgreSQL URL using the restricted app role and `sslmode=require`. **Secret.**
- `GOOGLE_CLIENT_ID` — Google OAuth web client ID. Public identifier, but configure on the API too.
- `SINOPIA_ALLOWED_ORIGINS` — exact HTTPS origins, comma-separated. Not secret.
- `SINOPIA_PROXY_SECRET` — at least 32 random characters shared with the frontend proxy. **Secret.**
- `SINOPIA_ENCRYPTION_KEYS` — active AES-GCM key first, optional older keys after it. **Secret.**
- `TURNSTILE_SECRET_KEY` — Cloudflare Turnstile server secret. **Secret.**
- `SINOPIA_TURNSTILE_HOSTNAMES` — approved hostnames. Not secret.
- `SINOPIA_TERMS_VERSION`, `SINOPIA_PRIVACY_VERSION` — current document versions. Not secret.
- `SINOPIA_TIMEZONE` — IANA timezone for server-assigned dates (e.g. `Africa/Lagos`). Not secret.
- `CRON_SECRET` — bearer secret for the scheduled retention endpoint. **Secret.**
- `SINOPIA_RETENTION_DAYS` — approved retention window in days (1–3650). Not secret; do not set until the retention policy is approved.

Keep `DATABASE_OWNER_URL` out of the running API environment; it is for one-time owner migrations only.

### Coach app project (root directory `frontend/`)
- `VITE_API_BASE=/api` — public path to the same-origin Vercel proxy.
- `SINOPIA_BACKEND_URL` — server-only API origin used by the proxy. **Do not prefix with `VITE_`.**
- `SINOPIA_PROXY_SECRET` — server-only proxy secret matching the API project. **Secret.**
- `VITE_GOOGLE_CLIENT_ID` — public Google OAuth client ID; must match `GOOGLE_CLIENT_ID`.
- `VITE_TURNSTILE_SITE_KEY` — public Cloudflare Turnstile site key.
- `VITE_LEGAL_BASE_URL` — public landing/legal site origin.

### Landing/legal project (root directory `landing/`)
- `VITE_COACH_APP_URL` — deployed coach-app origin, without a path suffix.
- `VITE_CONTACT_EMAIL` — monitored public privacy contact.

The repository's `.env.example`, `frontend/.env.example`, and `landing/.env.example` contain local templates. Replace example domains and verify every hosted setting before deployment.


## Privacy and operational documents

The public privacy notice, terms, and deletion information are available from the landing application at /privacy, /terms, and /delete-account. These are drafts that require qualified legal review and completion of all placeholders before launch.

Operational drafts are in docs/data-map.md, docs/dpia.md, docs/breach-response.md, and docs/play-store-checklist.md. The security.txt template under .well-known must be completed with a monitored contact and canonical public URL before release.

## Known gaps before production

The first-party `/api/*` Vercel proxy is present, and the athlete history view includes workload/wellness charts plus a self-reported pain-region map; the app collects no geographic coordinates, so it does not produce a geographic map. The custom proxy secret, domain, exact production CSP, Cloudflare edge rule, configured retention policy/cron secret, inactivity warnings, PostgreSQL runtime configuration, and hosted preview tests still require verification. Confirm actual subprocessors and processing regions, test deletion across backups, and complete an independent security and privacy review before collecting real athlete data.


## Application-level encryption

In production, Sinopia refuses to start without SINOPIA_ENCRYPTION_KEYS. Configure a comma-separated key ring in the host secret manager, with the active key first and any older decryption keys after it. Each value must be a unique key ID followed by a colon and a base64url-encoded 32-byte key. Generate a key locally with Python using secrets.token_bytes(32) and base64.urlsafe_b64encode; never commit it. Athlete labels and pain-area values are encrypted using AES-GCM. The PostgreSQL owner migration re-encrypts stored labels and pain-area values and rebuilds keyed duplicate-label digests using the configured active key. Keep old keys in the key ring during migration and until backups using them have expired. The migration must be run and verified against a backup before key rotation is considered complete.


## Hosting and user feedback

Use [the launch checklist](docs/launch-checklist.md) to configure the backend, the coach frontend, and the landing/legal site. The coach frontend includes a same-origin Vercel Edge proxy at `/api/*`; configure the server-side `SINOPIA_BACKEND_URL` environment variable in Vercel and allow the exact coach frontend origin in the backend. The coach project must set `VITE_API_BASE=/api`, Google/Turnstile public IDs, the server-only proxy origin/secret, and the legal URL. The landing project must set the deployed coach origin and a monitored contact address. These deployment values are deliberately not guessed or committed.

The branch is suitable only for a synthetic-data preview after the latest CI passes and hosting configuration is verified. A short, privacy-preserving tester script is included in `docs/launch-checklist.md`. It is not cleared for real athlete or child health data while retention automation, hosted auth/RLS/deletion tests, key recovery, legal/privacy review, provider configuration, and the remaining operational controls are outstanding.
