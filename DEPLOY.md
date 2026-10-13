# Deploying Sinopia on free tiers

Everything below is free tier only: Vercel Hobby for the two frontends,
Render's free web service for the FastAPI backend, and Tiger Cloud's
free Postgres plan for the database, which is external on purpose and
not one of Render's own databases.

## 1. External free Postgres (Tiger Cloud)

1. Create an account at tigerdata.com and open a free Postgres service.
2. Copy the connection string, it looks like
   `postgresql://user:password@host:port/dbname`.
3. That value becomes `DATABASE_URL` on the backend. Free plan limits
   are far above what this three-table app needs.

## 2. Backend on Render (free web service)

1. Push this repo or point a blank Web Service on Render at it.
2. Render can also read `render.yaml` straight from the repo root; it
   sets a Python runtime, free plan, `pip install -r requirements.txt`
   and `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
3. In the service's Environment tab set:
   - `DATABASE_URL` from step 1
   - `GOOGLE_CLIENT_ID`, the Google OAuth client id from step 3
   - `SINOPIA_ALLOWED_ORIGINS`, comma-separated origins of the two
     Vercel frontends, for example
     `https://sinopia-landing.vercel.app,https://sinopia-app.vercel.app`
   - `GROQ_API_KEY` only if the plain-language explain endpoint should
     use its LLM; without it a deterministic template is used.

## 3. Google sign-in client id (needed by both frontends and the backend)

1. In Google Cloud Console create an OAuth client of type Web
   application. No redirect URIs and no client secret are needed for
   the ID token flow.
2. Under Authorized JavaScript origins add both Vercel origins from
   step 4 and, for local work, `http://localhost:5173` and
   `http://localhost:5174`.
3. The resulting client id is `GOOGLE_CLIENT_ID` on the backend and
   `VITE_GOOGLE_CLIENT_ID` on the frontend.

## 4. Frontends on Vercel (Hobby)

Two separate Vercel projects, one per folder:

1. Landing: import the repo into a Vercel project, set Root Directory
   to `landing`, Framework Preset Vite. Environment:
   - `VITE_COACH_APP_URL`, the production URL of the coach tool
2. Coach tool: a second project, Root Directory `frontend`. Environment:
   - `VITE_API_URL`, the Render backend URL, for example
     `https://sinopia-backend.onrender.com`
   - `VITE_GOOGLE_CLIENT_ID` from step 3

Both folders ship a `vercel.json`; the frontend one enables the SPA
rewrite so `/checkin/{code}` pages render after a fresh load.

## 5. Verify after deploy

- Open the landing page: About, privacy note, the not-a-medical-tool
  line and the try the demo button all render.
- Try the demo reaches the demo dashboard of fake `DEMO-*` athletes
  with no sign-in.
- Sign in with Google on the coach tool, create a team, add an athlete
  code, log a session, and see a status row.
- A second Google account gets its own empty team and sees no rows
  from the first coach's team.
