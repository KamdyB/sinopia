# Sinopia

A prevention delivery layer for coaches of school and youth sports
teams in low-resource settings. Full documentation lands in a later
phase.

Sinopia is not a medical tool. It never diagnoses, and it never stores
athlete names: athletes are opaque codes, and every record belongs to
one coach-verified team.

## What is inside

- `backend/` FastAPI. The scoring engine in `backend/scoring/` is
  deliberately untouched by anything in this repo's deployment work.
- `frontend/` Vite + React coach dashboard for the signed-in coach.
- `landing/` Vite + React landing page and About page.
- `tests/` pytest suite (36 tests, run with `python -m pytest -q`).

## Demo mode

No login needed. `GET /demo/statuses` and
`GET /demo/athletes/{code}/history` serve fake athletes with codes like
`DEMO-A1`, built from hand-written demo numbers and run through the
real rules engine. It is read-only and never touches real data.

## Running locally

Backend:

```
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

The backend uses SQLite at `SINOPIA_DB_PATH` when `DATABASE_URL` is
unset, and PostgreSQL when it is set.

Frontend: `cd frontend && npm install && npm run dev`
Landing: `cd landing && npm install && npm run dev`
Tests: `python -m pytest -q`

After `npm run build` in both frontend projects, deploy with `vercel`.

## Deploying on free tiers

See DEPLOY.md for the full walkthrough: the frontend and landing page
go to Vercel, the backend goes to Render's free tier, and the database
goes to an external free Postgres (Tiger Cloud), deliberately not
Render's own database.
