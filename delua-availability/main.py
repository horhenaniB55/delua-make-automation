"""Delua availability microservice (FastAPI).

Reads busy times from Google Calendar (service account, read-only) and
serves the booking form's availability checks. Response shapes match the
Make webhook arms, so the form only needs a URL swap for reads; booking
submit (action=book) stays on the Make webhook.

  GET /healthz
  GET /api/availability?date=YYYY-MM-DD&package=Basic|Premium
  GET /api/month?from=YYYY-MM-DD&to=YYYY-MM-DD&package=Basic|Premium
"""
import json
import os
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from slots import MANILA, compute_free_slots, month_full_dates, parse_day

CALENDAR_ID = os.getenv("CALENDAR_ID", "your-gmail@gmail.com")
ORIGINS = [o.strip() for o in os.getenv(
    "ORIGINS",
    "https://your-custom-web.com,http://localhost:8080").split(",")]

app = FastAPI(title="Delua availability")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _calendar():
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as e:  # pragma: no cover
        raise HTTPException(500, f"google client libs missing: {e}")
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not raw:
        raise HTTPException(500, "GOOGLE_SERVICE_ACCOUNT_JSON not set")
    creds = service_account.Credentials.from_service_account_info(
        json.loads(raw),
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
    )
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _to_dt(v: str) -> datetime:
    dt = datetime.fromisoformat(v)
    return dt if dt.tzinfo else dt.replace(tzinfo=MANILA)


def fetch_busy(from_dt: datetime, to_dt: datetime):
    """Busy (start, end) pairs in [from_dt, to_dt). All-day events = whole day."""
    svc = _calendar()
    try:
        items = svc.events().list(
            calendarId=CALENDAR_ID,
            timeMin=from_dt.isoformat(),
            timeMax=to_dt.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=250,
        ).execute().get("items", [])
    except Exception as e:
        raise HTTPException(502, f"calendar read failed: {e}")
    busy = []
    for ev in items:
        s, e = ev.get("start", {}), ev.get("end", {})
        if "dateTime" in s and "dateTime" in e:
            busy.append((_to_dt(s["dateTime"]), _to_dt(e["dateTime"])))
        elif "date" in s:
            d0 = parse_day(s["date"])
            d1 = parse_day(e.get("date", s["date"]))
            busy.append((
                datetime(d0.year, d0.month, d0.day, tzinfo=MANILA),
                datetime(d1.year, d1.month, d1.day, tzinfo=MANILA),
            ))
    return busy


def _day_bounds(day_str: str):
    d = parse_day(day_str)
    start = datetime(d.year, d.month, d.day, tzinfo=MANILA)
    return start, start + timedelta(days=1)


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/api/availability")
def availability(date: str = Query(pattern=r"^\d{4}-\d{2}-\d{2}$"),
                 package: str = "Basic"):
    start, end = _day_bounds(date)
    slots = compute_free_slots(date, package, fetch_busy(start, end))
    return {"date": date, "package": package, "slots": slots}


@app.get("/api/month")
def month(from_: str = Query(alias="from",
                             pattern=r"^\d{4}-\d{2}-\d{2}$"),
            to: str = Query(pattern=r"^\d{4}-\d{2}-\d{2}$"),
            package: str = "Basic"):
    f = datetime(*parse_day(from_).timetuple()[:3], tzinfo=MANILA)
    t = datetime(*parse_day(to).timetuple()[:3], tzinfo=MANILA)
    full = month_full_dates(from_, to, package, fetch_busy(f, t))
    return {"full": full}
