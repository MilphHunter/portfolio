from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
}
WDN = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def infer_year(month_str: str, day: int, weekday_str: str, tz: str = "America/New_York") -> date | None:
    m = MONTHS[month_str.strip().lower()[:3]]
    w = weekday_str.strip().title()[:3]  # "Tue", "Mon", ...
    today = datetime.now(ZoneInfo(tz)).date()

    limit = today + timedelta(days=366*3)
    d = today
    while d <= limit:
        if d.month == m and d.day == day and WDN[d.weekday()] == w:
            return d
        d += timedelta(days=1)
    return None


found = infer_year("May", 26, "Tue", tz="America/New_York")