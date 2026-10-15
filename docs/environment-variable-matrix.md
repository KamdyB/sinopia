# Sinopia environment-variable setup matrix

This matrix documents the current main-branch environment contract; provider values must still be verified in their dashboards. It is a configuration guide, not proof that a provider has been configured. Set variables in the specific project/runtime that consumes them. Never paste real secrets into GitHub source, issue comments, chat, or any `VITE_*` variable.

## 1. API runtime (Vercel API project, or the selected backend host)

| Variable | Required value | Secret? |
|---|---|---|
| `SINOPIA_ENV` | `production` in production. For local development only, `development`. | No |
| `DATABASE_URL` | Neon PostgreSQL connection URL for the restricted application role, preferably pooled, with TLS/SSL required. Do not use the owner role. | **Yes** |
| `GOOGLE_CLIENT_ID` | OAuth 2.0 Web client ID from Google Cloud. Must match the frontend's client ID and authorized origins. | No; public identifier |
| `RESEND_API_KEY` | Backend-only Resend API key used to send email verification links. | **Yes** |
| `SINOPIA_EMAIL_FROM` | Sender address on a domain verified with Resend. | No |
| `SINOPIA_EMAIL_APP_URL` | Exact HTTPS origin of the coach app, with no path. | No |
| `SINOPIA_EMAIL_TOKEN_SECRET` | Random secret of at least 32 characters used to sign 15-minute verification links. | **Yes** |
| `SINOPIA_ALLOWED_ORIGINS` | Exact production coach-app origin(s), comma-separated, e.g. `https://app.your-owned-domain.example`; no paths or wildcard. | No |
| `SINOPIA_PROXY_SECRET` | Random high-entropy value at least 32 characters long. Use the **same value** in the API runtime and coach frontend Vercel server environment. Generate a different value from every other secret. | **Yes** |
| `SINOPIA_ENCRYPTION_KEYS` | Key ring format `active-key-id:BASE64URL_32_BYTE_KEY`; older keys may follow comma-separated while still needed for decrypting data/backups. Generate locally; never commit or share. | **Critical secret** |
| `TURNSTILE_SECRET_KEY` | Secret key for the Turnstile widget configured for the coach app hostname. | **Yes** |
| `SINOPIA_TURNSTILE_HOSTNAMES` | Exact hostname(s) allowed by Turnstile, comma-separated, e.g. `app.your-owned-domain.example`; hostname only, no scheme/path. | No |
| `SINOPIA_TERMS_VERSION` | Version/date identifier matching the actual published terms, e.g. `2026-10-15` only after that version is published. | No |
| `SINOPIA_PRIVACY_VERSION` | Version/date identifier matching the actual published privacy notice. | No |
| `SINOPIA_TIMEZONE` | IANA timezone for the pilot, e.g. `Africa/Lagos` if that is the pilot team's timezone. | No |
| `CRON_SECRET` | At least 32 random characters; used as the bearer secret for the daily Vercel retention cron. Configure only in the API runtime. | **Yes** |
| `SINOPIA_RETENTION_DAYS` | Data-controller-approved retention window, integer 1–3650. Leave unset until a policy is approved; missing/invalid values make the job fail closed. | No |
| `GROQ_API_KEY` | A Groq API key only if the current explain/AI feature is intended to use Groq; otherwise leave unset and verify that the feature handles absence safely. | **Yes** |
| `SINOPIA_DB_PATH` | Local SQLite path for development only, e.g. `sinopia.db`. Do not rely on local filesystem storage in a serverless production deployment. | No |

## 2. Coach frontend Vercel project (root directory: `frontend/`)

| Variable | Required value | Secret? |
|---|---|---|
| `VITE_API_BASE` | Production: `/api` to use the same-origin Vercel proxy; its rewrite must run before the SPA fallback. Local dev may use `http://localhost:8000`. | No |
| `VITE_GOOGLE_CLIENT_ID` | Same Google OAuth Web client ID as API's `GOOGLE_CLIENT_ID`. | No; public identifier |
| `VITE_TURNSTILE_SITE_KEY` | Public/site key paired with API's `TURNSTILE_SECRET_KEY`, restricted to the coach app hostname. | No; designed to be public |
| `VITE_LEGAL_BASE_URL` | Absolute origin of the deployed landing/legal site, e.g. `https://www.your-owned-domain.example`. | No |
| `SINOPIA_BACKEND_URL` | Server-side origin of the API deployment, e.g. `https://your-api-project.vercel.app`; use the real deployed origin, no invented placeholder in production. | No, but server-only |
| `SINOPIA_PROXY_SECRET` | Exact same secret value configured on the API runtime. Must **not** have a `VITE_` prefix. | **Yes** |

## 3. Landing/legal Vercel project (root directory: `landing/`)

| Variable | Required value | Secret? |
|---|---|---|
| `VITE_COACH_APP_URL` | Absolute origin of the deployed coach app, e.g. `https://app.your-owned-domain.example`. | No |
| `VITE_CONTACT_EMAIL` | A real, monitored privacy/contact email address that the project operator controls. Do not leave blank for public launch. | Public contact information, not a secret |

## 4. One-time Neon migration environment (local trusted machine only)

| Variable | Required value | Secret? |
|---|---|---|
| `DATABASE_OWNER_URL` | Neon connection URL for the owner/migration role. Use only for reviewed schema migration, never as the app runtime's `DATABASE_URL`. Unset it after migration. | **Yes** |
| `SINOPIA_DB_APP_ROLE` | Exact database role name created for the restricted application runtime; must not own RLS tables or have `BYPASSRLS`. | No |

Do not add migration-only variables to the production API runtime unless a documented migration procedure specifically requires them.

## 5. Generate secrets safely

- Proxy secret: generate a fresh random value with a password manager or a cryptographically secure local generator; use the identical value only in the API and frontend server-side proxy settings.
- Encryption key: generate 32 random bytes and encode with URL-safe Base64. Assign a unique key ID. Store the key ring in the provider's encrypted environment-variable settings and a separately secured recovery location.
- Google OAuth: create a Web application OAuth client, configure the actual production origins and callback/authorized JavaScript origins required by the Google Identity flow, then use its client ID in both places. Do not put a client secret in the browser.
- Cloudflare Turnstile: create a widget for the real coach-app hostname, set its public site key in the frontend and secret key in the API, and verify the returned hostname/action in a hosted test.
- Neon: create separate owner/migration and restricted application roles. The API must use only the restricted role. Never place a Neon URL in frontend variables or client bundles.

## 6. Deployment targets and status

- GitHub repository variables/secrets are for CI workflows only when workflows explicitly read them. They do **not** automatically configure Vercel, Neon, or Cloudflare.
- Put runtime values in the correct Vercel project's Environment Variables (Production, and Preview only when intentionally testing). Redeploy after changing values.
- Put database credentials in the backend runtime only. Put Turnstile's secret key in the backend runtime only.
- Values with a `VITE_` prefix are compiled into browser-visible assets. Never place tokens, credentials, encryption keys, database URLs, allowlists, or proxy secrets in them.
- These are names and expected values from the current security branch's configuration docs. The actual deployment settings have not been independently inspected, so treat every provider setting as **not yet verified** until you check it in the dashboard and test the deployed app.
