# Sinopia data map

**Release status: not approved for real athlete data.** This document describes repository implementation, not a verified live deployment. Provider activation, hosted configuration, backup behaviour, and deletion across backups must be independently confirmed before launch.

## Data subjects and records

| Subject | Data | Purpose | Code-level storage and access |
|---|---|---|---|
| Coach | Google email, display name, account and policy-acceptance timestamps | Sign-in, team ownership, policy records | coaches and coach_sessions tables; coach session is server-side and team ownership is checked by the API |
| Team | Random team ID, team label/type, creation time | Scope records to a coach/team | teams table; access is intended to be restricted to the owning coach and PostgreSQL row-level security (RLS) context |
| Athlete | Random player ID, encrypted label, team category, registration date, hashed check-in token, consent-confirmation timestamp | Roster, check-in association and history | players table; label encryption and token hashing are implemented in the application |
| Training | Date, duration, perceived effort, team ID | Workload history | sessions, team_sessions, and open_team_sessions tables |
| Wellness check-in | Date, sleep, energy, soreness, stress, pain response, encrypted selected pain-area category, acknowledgement flag, team ID | A prompt for a coach-athlete conversation | checkins table; not a diagnosis or validated injury prediction |
| Security/operations | Hashed server-session token, expiry, audit event type/team/time, rate-limit bucket keys and counters, request IP used for throttling | Authentication, audit trail and abuse prevention | coach_sessions, audit_log, and rate_limit_buckets; IP should be used only as required for security controls, not analytics |

**Storage distinction:** development mode can use a local SQLite file. Production mode refuses to fall back to SQLite and requires DATABASE_URL; the PostgreSQL adapter, owner migration, RLS policies and shared rate-limit storage are implemented in the repository. This does not mean a Neon database, restricted app role, production environment variables, or hosted RLS behaviour has been configured or verified. Do not describe PostgreSQL as the live store until the actual API deployment is checked.

## Data flow

1. A coach signs in with Google. The backend verifies the ID token, applies the configured coach allowlist, and creates an opaque server-side session. The browser receives the session in an HttpOnly cookie.
2. Coach API operations are scoped to the coach's team. The API should return not-found responses for foreign-team athlete IDs; hosted isolation must still be tested against the restricted PostgreSQL role.
3. A coach can generate a separate random check-in token. The token is stored as a hash and placed in a URL fragment; the browser submits it in the request body. Token rotation invalidates an older link.
4. The athlete submits numeric self-reported wellness values and an optional fixed pain-area category. The backend associates the submission with the token's athlete. A team session may also ask for perceived effort and record workload.
5. The backend computes workload/status. If the optional Groq explanation is enabled, the prompt contains the computed status and generic reasons, not the athlete's name or raw wellness answers. Confirm provider terms and processing region before enabling it for any real data.
6. Coaches can export team data and delete records through supported application flows. A successful application deletion is not proof that copies in backups, logs, provider systems, or exports have also been erased.

## Encryption and identifiers

- Athlete labels and pain-area values use application-level AES-GCM encryption when the configured key ring is available; production refuses to start without the required encryption configuration.
- Duplicate athlete labels use a keyed digest rather than plaintext comparison.
- Check-in tokens are random and stored as hashes; server session tokens are stored as hashes.
- Encryption reduces exposure of selected fields but does not make the entire database, backups, logs, browser, or operator access risk-free. Protect keys separately, rehearse key recovery, and test restore before launch.

## Retention and deletion

- A daily Vercel Cron schedule is present for the internal retention purge endpoint. The endpoint fails closed and deletes nothing if CRON_SECRET or a valid, approved SINOPIA_RETENTION_DAYS value is missing.
- Retention policy must be approved by the data controller before the days value is set. The implemented purge targets old training sessions and check-ins; it does not automatically remove roster entries, account/session records, provider logs, exports, or backups.
- Inactivity warnings are not implemented.
- Verify a synthetic expired record is removed while a recent record remains, and document how backup expiry and restoration interact with deletion.
- Account/athlete deletion, export, and retention must be tested against the actual production database role and hosted API before any real data is collected.

## Providers and processing locations

These are code/repository intentions, not proof that a provider is currently configured or that a particular region is active.

- **Google:** coach identity verification. Confirm applicable terms and processing details.
- **Groq:** optional explanation service. Keep disabled until its processing terms, region, and data-handling arrangements are approved.
- **Vercel:** intended hosting for frontend, landing/legal site, API proxy and scheduled retention. Verify each project's root directory, region, environment variables, logs and deployment status.
- **Neon PostgreSQL:** intended production database. Confirm region, TLS, owner/restricted roles, pooled connection URL, backups, RLS and recovery.
- **Cloudflare:** intended DNS/edge protection and Turnstile. Confirm actual domain, HTTPS mode, edge rules, hostnames and secret configuration.

Before launch, record actual providers/subprocessors, data-processing terms, regions, retention periods, backup behaviour, and responsible controller/contact details. Do not claim intended providers are active subprocessors until verified.

## Outstanding release conditions

- [ ] Confirm the production API uses PostgreSQL with a restricted non-owner, non-BYPASSRLS role and prove cross-team isolation against the hosted deployment.
- [ ] Verify all environment variables, proxy secret boundaries, Google OAuth origins, Turnstile, Cloudflare rules, HTTPS and security headers.
- [ ] Pass hosted auth/session rotation/logout, export/deletion, rate-limit, retention and backup/restore tests.
- [ ] Establish key backup/recovery and rotation procedures; test encrypted-data round trips after migration and restore.
- [ ] Complete the controller's retention policy, guardian/appropriate consent process, legal/privacy review, contact details, provider terms and processing-region review.
- [ ] Keep pilot data synthetic until all release gates have evidence. Never use this prototype to diagnose or make medical decisions.
