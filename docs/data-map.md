# Sinopia data map

**Status:** implementation draft. Verify this map against the actual production deployment before collecting real athlete data.

## Data subjects and records

| Subject | Data | Purpose | Current storage / access |
|---|---|---|---|
| Coach | Google email, display name, account and policy-acceptance timestamps | Sign-in, team ownership, declarations | SQLite coaches and coach_sessions; authenticated coach |
| Team | Random team ID, team label, creation time | Isolate records by coach | SQLite teams; owning coach |
| Athlete | Random player ID, athlete label/code, team category, registration date, check-in token | Roster and history association | SQLite players; owning coach; token used by athlete for check-in |
| Training | Date, duration, perceived effort, team ID | Workload history | SQLite sessions; owning coach |
| Wellness check-in | Date, sleep, energy, soreness, stress, pain response, selected pain-area category, acknowledgement flag, team ID | Coach conversation prompt | SQLite checkins; owning coach |
| Security | Hashed server-session token, expiry, session cookie, request IP for throttling | Session validation and abuse prevention | SQLite coach_sessions and process memory; not intended for analytics |

## Data flow

1. Coach signs in with Google. The backend verifies the Google ID token and creates a random server-side session. Only the session token is sent to the browser in an HttpOnly cookie.
2. Coach requests are scoped to the coach's team ID. Unknown or foreign-team athlete IDs return 404.
3. Coach creates a check-in link. The backend generates a separate random token; the public page validates the token without returning an athlete name or ID.
4. Athlete sends numeric self-report answers and a fixed pain-area category. The backend associates the token with the athlete and stores the check-in.
5. The scoring engine calculates status inside the backend. If the optional Groq explanation feature is enabled, only the computed level and generic reasons are sent to Groq.
6. The coach may export that team's records as JSON or CSV or permanently delete the coach account and active team data.

## Providers and locations

- Google: coach identity verification. Google processing location and applicable terms must be confirmed.
- Groq: optional generic explanation request. Disable the feature if its processing terms or region are not approved.
- Vercel: intended frontend hosting, if selected. Confirm project region and logs.
- Render: intended backend hosting, if selected. Confirm service region and logs.
- Neon: planned PostgreSQL provider only if the SQLite-to-PostgreSQL migration is completed. It is not the current store in this branch.

Confirm the real providers, subprocessors, processing regions, retention settings, backups, and contractual terms before launch. Do not describe intended providers as active subprocessors until verified.

## Important implementation gaps

- Application-level encryption of athlete labels and pain-area values is not implemented.
- Automated 12-month retention and inactive-account warning are not implemented.
- The current SQLite stores need a controlled migration plan for pre-existing records with no team ID. Do not automatically assign legacy records to a coach.
- Shared/distributed rate limiting is not implemented; current throttles are process-local.
- Verify database backups and deletion propagation before claiming all copies are erased.
