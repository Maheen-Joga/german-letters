"""Public holidays in Germany, nationwide and per state, computed without any data file.

Easter Sunday comes from the anonymous Gregorian algorithm; the movable holidays are fixed
offsets from it. Holidays that apply only in some municipalities (Fronleichnam in parts of
Saxony and Thuringia, Mariä Himmelfahrt in Catholic parts of Bavaria, the Augsburg peace festival)
are not included, so a deadline computed for those places can be one day early, never late.
"""
from __future__ import annotations

from datetime import date, timedelta

STATES = ("BW", "BY", "BE", "BB", "HB", "HH", "HE", "MV", "NI", "NW", "RP", "SL", "SN", "ST", "SH", "TH")
REGIONS = ("DE", *STATES)

_ONE_OFF = {
    "BE": {date(2020, 5, 8): "Tag der Befreiung (einmalig)", date(2025, 5, 8): "Tag der Befreiung (einmalig)",
           date(2028, 6, 18): "75. Jahrestag des Volksaufstands 1953 (einmalig)"},
}


def easter(year: int) -> date:
    a, b, c = year % 19, year // 100, year % 100
    d, e = divmod(b, 4)
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 19 * l) // 433
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def _buss_und_bettag(year: int) -> date:
    """The Wednesday before 23 November."""
    d = date(year, 11, 22)
    return d - timedelta(days=(d.weekday() - 2) % 7)


def holidays(year: int, region: str = "DE") -> dict[date, str]:
    if region not in REGIONS:
        raise ValueError(f"unknown region {region!r}; choose from {list(REGIONS)}")
    ostern = easter(year)
    out = {
        date(year, 1, 1): "Neujahr",
        ostern - timedelta(days=2): "Karfreitag",
        ostern + timedelta(days=1): "Ostermontag",
        date(year, 5, 1): "Tag der Arbeit",
        ostern + timedelta(days=39): "Christi Himmelfahrt",
        ostern + timedelta(days=50): "Pfingstmontag",
        date(year, 10, 3): "Tag der Deutschen Einheit",
        date(year, 12, 25): "1. Weihnachtstag",
        date(year, 12, 26): "2. Weihnachtstag",
    }
    r = region
    if r in {"BW", "BY", "ST"}:
        out[date(year, 1, 6)] = "Heilige Drei Könige"
    if (r == "BE" and year >= 2019) or (r == "MV" and year >= 2023):
        out[date(year, 3, 8)] = "Internationaler Frauentag"
    if r in {"BW", "BY", "HE", "NW", "RP", "SL"}:
        out[ostern + timedelta(days=60)] = "Fronleichnam"
    if r == "SL":
        out[date(year, 8, 15)] = "Mariä Himmelfahrt"
    if r == "TH" and year >= 2019:
        out[date(year, 9, 20)] = "Weltkindertag"
    if (r in {"BB", "MV", "SN", "ST", "TH"} or (r in {"HB", "HH", "NI", "SH"} and year >= 2018)
            or year == 2017):
        out[date(year, 10, 31)] = "Reformationstag"
    if r in {"BW", "BY", "NW", "RP", "SL"}:
        out[date(year, 11, 1)] = "Allerheiligen"
    if r == "SN":
        out[_buss_und_bettag(year)] = "Buß- und Bettag"
    out.update({d: n for d, n in _ONE_OFF.get(r, {}).items() if d.year == year})
    return dict(sorted(out.items()))


def holiday_name(day: date, region: str = "DE") -> str | None:
    return holidays(day.year, region).get(day)
