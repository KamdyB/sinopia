# Sinopia launch checklist

**Release state: private alpha preparation. Not approved for real athlete health data.**

## Deploy the coach API

1. Create a backend service from this repository using Python and the repository root.
2. Build command: `pip install -r requirements.txt`.
3. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
4. Use a durable, access-controlled database volume for a synthetic-data alpha only. The current application uses SQLite; do not treat ephemeral filesystem storage as durable.
5. Set `SINOPIA_ENV=production`, `SINOPIA_ALLOWED_ORIGINS` to the exact HTTPS origin of the coach frontend, `GOOGLE_CLIENT_ID`, `SINOPIA_ENCRYPTION_KEYS`, `SINOPIA_TERMS_VERSION`, and `SINOPIA_PRIVACY_VERSION`. Set `SINOPIA_DB_PATH` to the durable volume path. Do not use the development coach in a public deployment.
6. Generate a random 32-byte encryption key, base64url-encode it, and store it only in the host's secret manager. Never place the key in Git or a frontend variable.
7. Verify the API health endpoint, Google OAuth audience and authorised origins, exact CORS origin, secure session cookie, and that missing production secrets make startup fail closed.

## Deploy the coach frontend

1. Create a Vercel project with root directory `frontend`.
2. Add `SINOPIA_BACKEND_URL` as a server-side environment variable containing the backend origin only, such as `https://your-service.example`. Do not use a `VITE_` prefix for this secret/configuration.
3. Set `VITE_API_BASE=/api`, `VITE_GOOGLE_CLIENT_ID` to the same Google OAuth web client ID used by the backend, and `VITE_LEGAL_BASE_URL` to the public landing-site origin.
4. The Vercel edge function at `/api/*` proxies to the backend, preserving the session cookie and original Origin while removing client-supplied forwarded-IP headers. Add the exact coach frontend origin to `SINOPIA_ALLOWED_ORIGINS` on the backend.
5. Confirm that `/api/auth/me` returns 401 while signed out, sign-in sets an HttpOnly/Secure/SameSite cookie, logout clears it, and no session token appears in browser storage.

## Deploy the landing and legal pages

1. Create a second Vercel project with root directory `landing`.
2. Set `VITE_COACH_APP_URL` to the deployed coach frontend origin and `VITE_CONTACT_EMAIL` to a monitored privacy/security contact address.
3. Replace the controller/contact placeholders in `landing/src/LegalPage.tsx`; confirm the actual hosting providers, processing regions, retention policy, and subprocessors.
4. Have the privacy notice, terms, DPIA, and consent process reviewed by a qualified Nigerian privacy professional before real athlete data is collected.

## Synthetic-data feedback test

- Use only fictional athlete labels and synthetic training/check-in values.
- Ask testers to evaluate sign-in, onboarding, adding a fictional athlete, creating a check-in link, submitting one synthetic check-in, viewing the dashboard, export, and deletion.
- Do not use real minors, real injury/pain reports, real training records, or real team rosters in this alpha.
- Collect product feedback without analytics/tracking. Ask testers to report confusing wording, failed steps, accessibility problems, and expected missing workflows.

## Blockers before a real-data pilot

- Migrate from SQLite to PostgreSQL/SQLAlchemy with a tested legacy-data migration and backup/restore plan.
- Implement and verify automated 12-month retention and inactivity warnings.
- Add shared rate limiting for multi-worker deployments and operational monitoring that never logs athlete names, check-in tokens, or pain-area values.
- Add team-level session records so missed attendance is distinguishable from missing session data.
- Complete deletion verification, encryption key backup/recovery, provider contracts/regions, and independent security/privacy review.
- Confirm the school/club authority, parent/guardian consent and athlete notice process, and the legal basis for processing health-related information about children.


## Short feedback script

Use the same questions for each synthetic-data tester. Do not request or collect athlete names, health information, screenshots containing real records, or credentials.

1. What did you think Sinopia was for before you used it?
2. Could you complete Google sign-in and understand the consent/authority declarations?
3. Could you add a fictional athlete code, create a check-in link, and understand what the athlete sees?
4. Could you record a fictional session and understand the difference between a building baseline and a load flag?
5. Could you find pain acknowledgement, export, and deletion controls without help?
6. Where did you hesitate, get an error, or expect a different result?
7. What is the single most important improvement before a small pilot?

Record only the step, severity, browser/device category, and a short description. Use no names or health data. Treat any security issue or cross-team exposure as a stop-ship issue rather than ordinary feedback.
