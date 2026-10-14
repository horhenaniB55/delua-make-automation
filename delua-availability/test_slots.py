"""Slot-math tests — no credentials needed (pure slots.py only)."""
from datetime import datetime

from slots import MANILA, compute_free_slots, month_full_dates

FUTURE = "2026-10-20"
NOW = datetime(2026, 10, 13, 8, 0, tzinfo=MANILA)  # morning, Manila


def busy(*pairs):
    return [(datetime(*s, tzinfo=MANILA), datetime(*e, tzinfo=MANILA))
            for s, e in pairs]


# 1. empty calendar
assert compute_free_slots(FUTURE, "Basic", [], NOW) == \
    ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
assert compute_free_slots(FUTURE, "Premium", [], NOW) == \
    ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]

# 2. overlapping event 10:30-11:30 knocks out 10:00 and 11:00 (Basic)
b = busy(((2026, 10, 20, 10, 30), (2026, 10, 20, 11, 30)))
assert compute_free_slots(FUTURE, "Basic", b, NOW) == \
    ["09:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"], \
    compute_free_slots(FUTURE, "Basic", b, NOW)

# 3. back-to-back is fine: event ending exactly at slot start doesn't block
b = busy(((2026, 10, 20, 9, 0), (2026, 10, 20, 10, 0)))
assert "10:00" in compute_free_slots(FUTURE, "Basic", b, NOW)
assert "09:00" not in compute_free_slots(FUTURE, "Basic", b, NOW)

# 4. past date -> nothing
assert compute_free_slots("2026-10-01", "Basic", [], NOW) == []

# 5. today buffer: all of today inside 2h -> nothing
late = datetime(2026, 10, 13, 22, 0, tzinfo=MANILA)
assert compute_free_slots("2026-10-13", "Basic", [], late) == []

# 6. today morning: only slots >= now+2h
assert compute_free_slots("2026-10-13", "Basic", [], NOW) == \
    ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]

# 7. all-day busy -> full month day
allday = [(datetime(2026, 10, 21, 0, 0, tzinfo=MANILA),
           datetime(2026, 10, 22, 0, 0, tzinfo=MANILA))]
assert month_full_dates("2026-10-20", "2026-10-22", "Basic", allday, NOW) == \
    ["2026-10-21"]

# 8. empty month -> nothing full (past dates count as full)
assert month_full_dates("2026-10-20", "2026-10-22", "Basic", [], NOW) == []
assert month_full_dates("2026-10-12", "2026-10-14", "Basic", [], NOW) == \
    ["2026-10-12"]

print("all slot tests passed")
