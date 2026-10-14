# Delua availability microservice (FastAPI)

Google Calendar checker for the booking form. Serves machine-readable
availability so browsing dates costs zero Make credits and zero AI calls.
Booking submit (`action=book`) stays on the Make webhook — Make remains
the authority on conflicts at submit time.

## Endpoints (same shapes as the Make arms)

- `GET /healthz` → `{"ok": true}`
- `GET /api/availability?date=YYYY-MM-DD&package=Basic|Premium`
  → `{"date": ..., "package": ..., "slots": ["09:00", ...]}`
- `GET /api/month?from=YYYY-MM-DD&to=YYYY-MM-DD&package=...`
  → `{"full": ["YYYY-MM-DD", ...]}`

Rules (mirror the Make arms): 09:00–18:00 Manila, hourly starts,
Basic 60 min / Premium 120 min, session ends by 18:00, 2h buffer today,
past dates empty.

## Run locally

```
pip install -r requirements.txt
copy .env.example .env   # fill in service-account JSON
uvicorn main:app --port 8000
```

Logic tests need no credentials: `python test_slots.py`

## Go-live checklist

1. Google Cloud → service account → key (JSON). Share
   `your-gmail@gmail.com` with its `client_email` (see busy times only).
2. Set env vars (`CALENDAR_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON`, `ORIGINS`).
3. Deploy (Render/Railway/Fly, or Vercel Python — see `vercel.json`).
4. Form wiring — in `delua-booking/index.html`, keep `HOOK` for book,
   point reads at the service:
   `fetch(SVC + '/api/month?from=..&to=..&package=..')` → `{full}`
   `fetch(SVC + '/api/availability?date=..&package=..')` → `{slots}`
   Response shapes are identical, so only the URLs change.
