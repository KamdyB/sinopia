# Sinopia launch checklist — verified release gates

**Status: NOT approved for production or real athlete data.** This document separates code-level checks from provider/dashboard checks. A checked box means the listed evidence exists; do not mark it complete based on configuration intent alone.

## Architecture

- Frontend: Vercel project rooted at `frontend/`.
- Landing/legal site: separate Vercel project rooted at `landing/`.
- API: Vercel Python runtime with the custom entrypoint `backend.main:app` in the root `pyproject.toml`. Vercel's current Python runtime documentation supports FastAPI. Use the repository root as the API project's root directory, then verify the preview deployment's routes, cookies, database pooling, startup behavior, and bundle size. If that preview fails those checks, use Render as the API host instead.
- Database: Neon PostgreSQL with `sslmode=require`; create separate owner and restricted application roles. API uses only the restricted role.
- DNS/TLS/edge protection: Cloudflare; app and API use subdomains of one owned domain. Keep the Google sign-in origin and cookie behavior verified in browser tests.
- Do not create provider projects until the code PR has passed CI and its unresolved gates have been reviewed.

## Data integrity and visualisation

- The athlete history uses one point per calendar date, combines multiple sessions on the same date, and includes check-in-only dates. CI tests these rules.
- Workload charts show session duration × perceived effort. Wellness charts show the four self-reported daily scores. The body-region map summarizes only reported pain-area categories.
- The app currently collects no athlete coordinates or venue locations, so it must not present a geographic map or infer locations. Any future geographic feature needs an explicit data purpose, consent/privacy review, validation, and map-specific tests.
- The workload and wellness thresholds are provisional, not validated injury predictions. Do not present a colour/status as a diagnosis or a proven risk probability.

## 20-point release checklist

| # | Requirement | Evidence / current status |
|---|---|---|
| 1 | No secrets in frontend source or build | **CI build scan configured; latest commit must pass.** CI scans both `frontend/dist` and `landing/dist` for `GROQ_API_KEY`, database URL patterns and known secret prefixes. Google client ID and API URL are public configuration. |
| 2 | Full-history secret scan | Gitleaks CI uses `fetch-depth: 0`. **Still verify 2FA, push-protection settings, and branch protection in GitHub.** Rotate any exposed key; history rewriting alone is insufficient. |
| 3 | Browser cannot access DB | **Design requirement.** Browser must call only the app/API; no Neon URL, database credential, or database Data API in either bundle. Build scan pending. |
| 4 | PostgreSQL RLS | **Migration and PostgreSQL RLS integration test added; CI result must pass on the latest commit.** Migration enables and FORCEs RLS on `players`, `team_sessions`, `open_team_sessions`, `sessions`, `checkins`, and `audit_log`. Policies use transaction-local `app.team_id`; check-in token lookup has a narrowly scoped player policy. Must run migration with owner role and prove team A cannot read team B rows using the non-owner app role, including a query without a WHERE clause. |
| 5 | Sensitive field encryption | AES-GCM encryption code exists for athlete labels and pain-area values. The owner migration re-encrypts labels/pain areas and rebuilds keyed duplicate-label hashes using the active key ring. **PostgreSQL round-trip, backup restore, and key-recovery tests are still required.** |
| 6 | Server-side auth | Google ID token verification and opaque server-side sessions exist. **Server-side invite allowlist enforced before account/team creation; hosted end-to-end auth tests pending.** |
| 7 | Record access isolation | Route code scopes athlete operations to team IDs and returns 404 for foreign athlete IDs. **PostgreSQL RLS integration tests and check-in-token cross-team tests pending.** |
| 8 | Field tampering | Pydantic request models use `extra="forbid"` on core write requests; server sets team, IDs, registration/session dates and consent timestamps. **Add tampering tests for every write endpoint.** |
| 9 | Session cookies | HttpOnly, Secure in production, SameSite=Lax and 8-hour expiry are configured. **Session rotation at login, cookie behavior, and server-side logout invalidation require tests.** |
| 10 | Password storage | No password login exists; do not add passwords. If added in future, use Argon2id. |
| 11 | Login rate limit | **Shared PostgreSQL counter implementation added.** Requires hosted trusted-proxy IP verification, concurrency tests, and a Cloudflare edge rule on auth routes. |
| 12 | Turnstile bot protection | **Code and fail-closed tests added** for sign-in and delete-account confirmation. Configure the site key and secret in provider dashboards, allow the real app hostname, and verify hosted flows before public preview. |
| 13 | Parameterized SQL | Store calls bind values through SQLAlchemy text statements. **Audit all query strings and migration code; no string-built user values.** |
| 14 | Input validation | Pydantic validation exists on primary routes. **Full route-by-route bounds/enums audit pending.** |
| 15 | Output escaping / CSP | React renders content as text and no upload/HTML-rendering feature is intended. **CSP must be tested against Google Identity script and the production frontend; current API CSP alone does not protect frontend responses.** |
| 16 | File uploads | No upload route is intended. **Automated route inventory test pending.** |
| 17 | Explicit response models | Main roster/history/session endpoints use response models. **Audit all auth, export, check-in, and error responses; ensure no session token, check-in token, or foreign-team identifiers leak.** |
| 18 | Security headers | API middleware sets content-type, frame, referrer, permissions, CSP and HSTS in production. **Verify frontend/landing headers at the edge too.** |
| 19 | HTTPS | **Provider setting not yet applied.** Cloudflare Full (strict), Always Use HTTPS, HSTS, and production rejection of non-HTTPS deployment URLs must be verified after domain setup. |
| 20 | Dependency scans | CI runs `npm audit --audit-level=high`, `pip-audit`, and Gitleaks. **Dependabot configuration and current audit results must be verified after the dependency change.** |

## Retention automation

- Root `vercel.json` schedules a daily request to `/internal/retention/purge`.
- Configure `CRON_SECRET` in the API Vercel project and ensure Vercel Cron sends its bearer authorization header.
- Agree the retention period with the data controller/legal reviewer, then set `SINOPIA_RETENTION_DAYS` to an integer from 1 to 3650. The application intentionally does not guess this policy.
- If either variable is absent or invalid, the endpoint fails closed without deleting records.
- The job deletes only sessions and check-ins older than the cutoff, team by team under the normal RLS context. Athlete roster entries are retained until a separate athlete/account deletion.
- After deployment, verify a synthetic expired record is purged and a recent record remains. Check the cron result in Vercel logs without logging athlete data.

## Beta access gate

- Add `SINOPIA_COACH_ALLOWLIST` as a server-only environment variable containing normalized coach email addresses.
- The backend must verify Google's ID token first, then reject any email not on the allowlist **before creating a coach, team, or session**. Missing/empty allowlist fails closed in production.
- Do not put the allowlist in any `VITE_*` variable or frontend code.
- Turnstile server verification is a separate release blocker; the widget's client result alone is not trusted.

## PostgreSQL setup and migration

1. Create a Neon PostgreSQL database with TLS. Create separate owner/migration and restricted application roles in Neon.
2. Set `DATABASE_OWNER_URL` locally/temporarily for the migration role and `SINOPIA_DB_APP_ROLE` to the exact app role. Run `python -m backend.migrate` once.
3. Set `DATABASE_URL` only on the API host to the restricted role's pooled connection URL. The code appends `sslmode=require` if absent. Configure `SINOPIA_TIMEZONE` to the actual pilot team's timezone. Set the same high-entropy `SINOPIA_PROXY_SECRET` only in the API and Vercel frontend server environments.
4. Confirm the app role is not owner of RLS tables and does not have `BYPASSRLS`. The app must never connect with the owner URL.
5. Run PostgreSQL integration tests: migration idempotence; encrypted label/pain-area round trip; one check-in per athlete/day; team A cannot read/write team B; token-only check-in lookup; rate limits shared across independent workers; export/delete; backup and restore.
6. Existing local SQLite records are not automatically copied to Neon. If there is real data to preserve, stop and use a separately reviewed, tested migration and restore procedure. For synthetic-only alpha, start with an empty database.

## Hosting secrets (set only in provider dashboards)

API: `SINOPIA_ENV=production`, `SINOPIA_TIMEZONE` (IANA timezone for the pilot), `SINOPIA_PROXY_SECRET` (shared only with the Vercel API proxy), `DATABASE_URL` (restricted role), `GOOGLE_CLIENT_ID`, `SINOPIA_ALLOWED_ORIGINS` (exact HTTPS coach app origin), `SINOPIA_ENCRYPTION_KEYS`, `SINOPIA_COACH_ALLOWLIST`, `SINOPIA_TERMS_VERSION`, `SINOPIA_PRIVACY_VERSION`, `TURNSTILE_SECRET_KEY`, `SINOPIA_TURNSTILE_HOSTNAMES`, `TURNSTILE_SECRET_KEY`, `SINOPIA_TURNSTILE_HOSTNAMES`, and the server-only proxy secret.

Coach frontend: `SINOPIA_BACKEND_URL` (server-only API origin), `SINOPIA_PROXY_SECRET` (server-only shared secret), `VITE_GOOGLE_CLIENT_ID` (public), `VITE_TURNSTILE_SITE_KEY` (public), `VITE_API_BASE=/api`, `VITE_LEGAL_BASE_URL` (public). `SINOPIA_PROXY_SECRET` is server-only in the frontend Vercel project and API project; never prefix it with `VITE_`. The backend URL used by the proxy is server-only and must not be a `VITE_*` variable.

Landing: `VITE_COACH_APP_URL` and the public contact/legal configuration. Replace the legal controller/contact placeholders with verified details before launch.

## Do not launch until

- PostgreSQL migration and RLS tests pass with the restricted app role.
- Coach-email allowlist and Turnstile are implemented and tested.
- Both build outputs pass secret scans.
- Cookie rotation/logout, deletion, export, CSRF/CORS, HTTPS, security headers and team-isolation tests pass.
- Restore/recovery and deletion tests pass.
- Legal/privacy review, guardian consent process, controller identity/contact, processing regions and provider contracts are verified.
- The landing copy/demo matches the actual product; only fictional athlete data is used during alpha.

