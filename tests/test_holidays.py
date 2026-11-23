from datetime import date

import pytest

from german_letters.holidays import REGIONS, easter, holiday_name, holidays


@pytest.mark.parametrize("year, expected", [(2019, date(2019, 4, 21)), (2024, date(2024, 3, 31)),
                                            (2025, date(2025, 4, 20)), (2026, date(2026, 4, 5)), (2027, date(2027, 3, 28))])
def test_easter(year, expected):
    assert easter(year) == expected


@pytest.mark.parametrize("region, count", [("DE", 9), ("BE", 10), ("BY", 12), ("BW", 12), ("NW", 11), ("SL", 12),
                                           ("SN", 11), ("TH", 11), ("HH", 10), ("MV", 11)])
def test_holiday_counts_2026(region, count):
    assert len(holidays(2026, region)) == count


def test_state_specific_days():
    assert holiday_name(date(2026, 11, 18), "SN") == "Buß- und Bettag"
    assert holiday_name(date(2026, 9, 20), "TH") == "Weltkindertag"
    assert holiday_name(date(2026, 6, 4), "NW") == "Fronleichnam"
    assert holiday_name(date(2026, 6, 4), "BE") is None
    assert holiday_name(date(2026, 3, 8), "MV") == "Internationaler Frauentag"
    assert holiday_name(date(2022, 3, 8), "MV") is None


def test_reformation_day_rules():
    assert holiday_name(date(2017, 10, 31), "BY") == "Reformationstag"  # once, nationwide
    assert holiday_name(date(2017, 10, 31), "HH") == "Reformationstag"
    assert holiday_name(date(2016, 10, 31), "HH") is None
    assert holiday_name(date(2018, 10, 31), "HH") == "Reformationstag"
    assert holiday_name(date(2026, 10, 31), "BE") is None


def test_berlin_one_off_days():
    assert holiday_name(date(2025, 5, 8), "BE") and not holiday_name(date(2026, 5, 8), "BE")


def test_unknown_region():
    with pytest.raises(ValueError):
        holidays(2026, "XX")
    assert len(REGIONS) == 17
