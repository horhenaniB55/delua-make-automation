"""Pure slot math for Delua Studio booking. No Google/network deps — unit-testable.

Mirrors the Make availability rules:
  working hours 09:00-18:00 (Asia/Manila), hourly starts,
  Basic = 60 min, Premium = 120 min, session must end by 18:00,
  same-day bookings need 2h buffer, past dates have no slots.
"""
from datetime import date, datetime, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

MANILA = ZoneInfo("Asia/Manila")

DURATIONS_MIN = {"Basic": 60, "Premium": 120}
WORK_START_HR = 9
WORK_END_HR = 18
BUFFER_MIN = 120


def parse_day(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def overlaps(a_start: datetime, a_end: datetime,
             b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and a_end > b_start


def compute_free_slots(day_str: str, package: str,
                       busy: list[tuple[datetime, datetime]],
                       now: datetime | None = None) -> list[str]:
    """Return free hourly start times (["09:00", ...]) for one date.

    busy: iterable of (start, end) timezone-aware datetimes.
    """
    now = (now or datetime.now(MANILA)).astimezone(MANILA)
    day = parse_day(day_str)
    if day < now.date():
        return []
    duration = DURATIONS_MIN.get(package, 60)
    day_end = datetime(day.year, day.month, day.day,
                       WORK_END_HR, 0, tzinfo=MANILA)
    cutoff = now + timedelta(minutes=BUFFER_MIN)
    free: list[str] = []
    for h in range(WORK_START_HR, WORK_END_HR + 1):
        start = datetime(day.year, day.month, day.day, h, 0, tzinfo=MANILA)
        end = start + timedelta(minutes=duration)
        if end > day_end:
            continue
        if day == now.date() and start < cutoff:
            continue
        if any(overlaps(start, end, bs, be) for bs, be in busy):
            continue
        free.append(f"{h:02d}:00")
    return free


def month_full_dates(from_str: str, to_str: str, package: str,
                     busy: list[tuple[datetime, datetime]],
                     now: datetime | None = None) -> list[str]:
    """Dates in [from, to) with zero free slots, as YYYY-MM-DD."""
    now = (now or datetime.now(MANILA)).astimezone(MANILA)
    start = parse_day(from_str)
    end = parse_day(to_str)
    full: list[str] = []
    d = start
    while d < end:
        if not compute_free_slots(d.isoformat(), package, busy, now):
            full.append(d.isoformat())
        d += timedelta(days=1)
    return full
