from django.core.management.base import BaseCommand
from django.conf import settings
from apps.attendance.db import get_db
from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo

ZONE = ZoneInfo("Asia/Colombo")

def _parse_hhmm(s: str) -> time:
    hh, mm = s.split(":")
    return time(int(hh), int(mm))

LATE_START = _parse_hhmm(getattr(settings, "LATE_START_TIME", "09:10"))
LATE_CUTOFF = _parse_hhmm(getattr(settings, "LATE_CUTOFF_TIME", "12:00"))

def _is_workday(d: date) -> bool:
    # Mon=0 .. Sun=6
    return d.weekday() < 5

def _prev_workday(d: date) -> date:
    step = 1
    prev = d - timedelta(days=step)
    while not _is_workday(prev):
        step += 1
        prev = d - timedelta(days=step)
    return prev

def _to_local(utc_dt: datetime) -> datetime:
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(ZONE)

def _is_late_doc(doc) -> bool:
    """
    Late if inTime exists and local time is between [LATE_START, LATE_CUTOFF].
    """
    in_dt = doc.get("inTime")
    if not in_dt:
        return False
    loc = _to_local(in_dt)
    t = time(loc.hour, loc.minute, loc.second)
    return (t >= LATE_START) and (t <= LATE_CUTOFF)

def _iso_local_midnight_utc(d: date) -> datetime:
    # store notification date as local midnight converted to UTC
    local_midnight = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=ZONE)
    return local_midnight.astimezone(timezone.utc)

class Command(BaseCommand):
    help = "Detect late arrivals and create notifications for 3 and 5 consecutive days."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            dest="date_str",
            help="Target local date YYYY-MM-DD (defaults to yesterday in Asia/Colombo).",
        )

    def handle(self, *args, **opts):
        db = get_db()
        notif_col = db["notifications"]
        attend = db["attendance"]

        # indices (idempotent)
        notif_col.create_index(
            [("type", 1), ("empId", 1), ("date", 1), ("reason", 1)],
            unique=True,
            name="uniq_notif_per_reason_day_emp",
        )
        attend.create_index([("employeeCode", 1), ("date", 1)], name="emp_date_idx")

        # pick the target local date (yesterday by default)
        if opts.get("date_str"):
            target = datetime.strptime(opts["date_str"], "%Y-%m-%d").date()
        else:
            now_local = datetime.now(tz=ZONE)
            target = (now_local - timedelta(days=1)).date()

        if not _is_workday(target):
            self.stdout.write(self.style.WARNING(f"{target} is not a workday; nothing to do."))
            return

        # find all employees who have any attendance doc on the target date
        codes = attend.distinct("employeeCode", {"date": target.strftime("%Y-%m-%d")})
        self.stdout.write(f"Scanning {len(codes)} employee(s) for {target}")

        created_emp = created_hr = 0

        for code in codes:
            # get today's (target) doc
            today_doc = attend.find_one(
                {"employeeCode": code, "date": target.strftime("%Y-%m-%d")},
                {"inTime": 1, "outTime": 1, "employeeCode": 1, "date": 1},
            )
            # compute today's lateness
            today_late = bool(today_doc and _is_late_doc(today_doc))

            # compute consecutive streak ending today
            streak = 0
            if today_late:
                streak = 1
                # walk back previous workdays
                prev_day = _prev_workday(target)
                # look back at most 10 working days
                for _ in range(10):
                    prev_doc = attend.find_one(
                        {"employeeCode": code, "date": prev_day.strftime("%Y-%m-%d")},
                        {"inTime": 1},
                    )
                    if prev_doc and _is_late_doc(prev_doc):
                        streak += 1
                        prev_day = _prev_workday(prev_day)
                    else:
                        break

            # write optional flag onto today's attendance (non-breaking)
            if today_doc is not None:
                attend.update_one(
                    {"_id": today_doc["_id"]},
                    {"$set": {"isLate": today_late, "lateStreakToday": streak}},
                )

            # notifications
            if streak == 3:
                try:
                    notif_col.insert_one({
                        "to": code,
                        "type": "employee",
                        "empId": code,
                        "reason": "Late for 3 continuous days",
                        "date": _iso_local_midnight_utc(target),
                        "createdAt": datetime.now(tz=timezone.utc),
                        "meta": {"streak": 3}
                    })
                    created_emp += 1
                    self.stdout.write(self.style.SUCCESS(f"[3-day] Notified {code}"))
                except Exception:
                    # duplicate or write error -> ignore
                    pass

            if streak == 5:
                try:
                    notif_col.insert_one({
                        "to": "HR",
                        "type": "hr",
                        "empId": code,
                        "reason": "Late for 5 continuous days",
                        "date": _iso_local_midnight_utc(target),
                        "createdAt": datetime.now(tz=timezone.utc),
                        "meta": {"streak": 5}
                    })
                    created_hr += 1
                    self.stdout.write(self.style.SUCCESS(f"[5-day] Notified HR for {code}"))
                except Exception:
                    pass

        self.stdout.write(self.style.SUCCESS(
            f"Done. Employee notifications: {created_emp}, HR notifications: {created_hr}"
        ))
