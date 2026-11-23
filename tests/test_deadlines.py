from datetime import date

from german_letters import deadlines as dl

from .helpers import d


def test_add_months_clamps_to_month_end():
    assert dl.add_months(d("2026-01-31"), 1) == d("2026-02-28")
    assert dl.add_months(d("2024-01-31"), 1) == d("2024-02-29")
    assert dl.add_months(d("2026-12-15"), 1) == d("2027-01-15")
    assert dl.add_months(d("2026-03-15"), -1) == d("2026-02-15")


def test_working_days():
    assert dl.is_working_day(d("2026-11-23"))  # Monday
    assert not dl.is_working_day(d("2026-11-21"))  # Saturday
    assert dl.is_werktag(d("2026-11-21"))  # Saturday is a Werktag
    assert not dl.is_werktag(d("2026-12-25"))
    assert dl.shift_193(d("2026-12-25")) == d("2026-12-28")


def test_objection_uses_the_four_day_rule():
    o = dl.objection(d("2026-11-20"))
    assert o.when == d("2026-12-24") and "2026-11-24" in o.notes[0]


def test_objection_deadline_moves_off_a_weekend():
    # posted 2026-12-03 -> known 2026-12-07 -> 2027-01-07 (Thursday); posted 2026-12-05 -> 2027-01-09 (Saturday) -> Monday 11th
    assert dl.objection(d("2026-12-03")).when == d("2027-01-07")
    assert dl.objection(d("2026-12-05")).when == d("2027-01-11")


def test_objection_later_receipt_counts():
    assert dl.objection(d("2026-11-20"), received=d("2026-11-30")).when == d("2026-12-30")
    assert dl.objection(d("2026-11-20"), received=d("2026-11-22")).when == d("2026-12-24")  # earlier receipt does not shorten it


def test_withdrawal_14_days_and_christmas():
    assert dl.withdrawal(d("2026-11-23")).when == d("2026-12-07")
    assert dl.withdrawal(d("2026-12-11")).when == d("2026-12-28")


def test_third_werktag_counts_saturday_and_skips_holidays():
    assert dl.third_werktag(2026, 12) == d("2026-12-03")
    assert dl.third_werktag(2026, 8) == d("2026-08-04")  # Sat 1, Mon 3, Tue 4
    assert dl.third_werktag(2027, 1) == d("2027-01-05")  # Fri 1 is a holiday: Sat 2, Mon 4, Tue 5
    assert dl.third_werktag(2026, 10) == d("2026-10-05")  # Thu 1, Fri 2, Sat 3 is a holiday, Mon 5


def test_tenancy_notice():
    by, end = dl.tenancy_notice(d("2026-12-02"))
    assert (by.when, end.when) == (d("2026-12-03"), d("2027-02-28"))
    by, end = dl.tenancy_notice(d("2026-12-04"))
    assert (by.when, end.when) == (d("2027-01-05"), d("2027-03-31"))
    by, end = dl.tenancy_notice(d("2026-12-03"))  # on the cutoff itself
    assert end.when == d("2027-02-28")


def test_employment_notice_to_the_15th_or_month_end():
    assert dl.employment_notice(d("2026-11-02")).when == d("2026-11-30")
    assert dl.employment_notice(d("2026-11-03")).when == d("2026-12-15")
    assert dl.employment_notice(d("2026-11-17")).when == d("2026-12-15")
    assert dl.employment_notice(d("2026-11-18")).when == d("2026-12-31")
    assert dl.employment_notice(d("2027-01-31")).when == d("2027-02-28")
    assert dl.employment_notice(d("2027-02-01")).when == d("2027-03-15")


def test_employment_notice_in_probation_is_two_weeks():
    assert dl.employment_notice(d("2026-11-23"), probation=True).when == d("2026-12-07")


def test_contract_notice():
    assert dl.contract_notice(d("2026-11-23")).when == d("2026-12-23")
    assert dl.contract_notice(d("2026-11-23"), term_end=d("2027-03-31")).when == d("2027-03-31")
    late = dl.contract_notice(d("2027-03-15"), term_end=d("2027-03-31"))  # too late for the term end
    assert late.when == d("2027-04-15")


def test_data_access_reply():
    assert dl.data_access_reply(d("2026-11-30")).when == d("2026-12-30")
    assert dl.data_access_reply(d("2026-11-25")).when == d("2026-12-28")  # 25 Dec -> next working day


def test_region_changes_the_result():
    # 2027-01-06 is a holiday in Bavaria: a withdrawal starting 2026-12-23 ends 2027-01-06
    assert dl.withdrawal(d("2026-12-23"), "DE").when == date(2027, 1, 6)
    assert dl.withdrawal(d("2026-12-23"), "BY").when == date(2027, 1, 7)
