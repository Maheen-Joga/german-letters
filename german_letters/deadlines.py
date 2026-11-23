"""Deadlines for the letters in this package.

Counting follows §§ 187, 188 and 193 BGB: the day of the triggering event is not counted, a period
in months ends on the day with the same number (or the month's last day), and a deadline for a
declaration that falls on a Saturday, Sunday or public holiday moves to the next working day.
Where the law is disputed, the functions return the earlier, safe date and say so in `notes`.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date, timedelta

from .holidays import holiday_name

POST_FICTION_DAYS = 4  # § 41(2) VwVfG, § 37(2) SGB X, § 122(2) AO since 1 January 2025 (before: 3)


@dataclass(frozen=True)
class Deadline:
    label: str  # what the date means, in English
    when: date
    basis: str  # the legal basis
    notes: tuple[str, ...] = field(default=())


def add_months(d: date, months: int) -> date:
    """Same day number `months` later, or the last day of that month (§ 188(3) BGB)."""
    m = d.month - 1 + months
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def last_day_of_month(d: date) -> date:
    return date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])


def is_working_day(d: date, region: str = "DE") -> bool:
    """Monday to Friday and not a public holiday: the days § 193 BGB lets a deadline end on."""
    return d.weekday() < 5 and holiday_name(d, region) is None


def is_werktag(d: date, region: str = "DE") -> bool:
    """Monday to Saturday and not a public holiday (the everyday meaning, used in § 573c BGB)."""
    return d.weekday() < 6 and holiday_name(d, region) is None


def shift_193(d: date, region: str = "DE") -> date:
    while not is_working_day(d, region):
        d += timedelta(days=1)
    return d


def objection(posted: date, received: date | None = None, region: str = "DE") -> Deadline:
    """Widerspruch against an administrative decision sent by post (§ 70 VwGO, § 84 SGG, § 355 AO).

    The decision counts as delivered on the fourth day after posting, or later if it really arrived
    later. The month runs from the next day; an end on a weekend or holiday moves to the next working day.
    """
    known = posted + timedelta(days=POST_FICTION_DAYS)
    notes = [f"counted as delivered on {known.isoformat()}: the fourth day after the date the authority posted it "
             "(the date on the letter is usually the posting date)"]
    if received and received > known:
        known = received
        notes.append("you received it later than that, so the later date counts; keep the envelope as evidence")
    end = add_months(known, 1)
    shifted = shift_193(end, region)
    if shifted != end:
        notes.append(f"{end.isoformat()} is a weekend or holiday, so the deadline moves to {shifted.isoformat()}")
    notes.append("the objection must arrive by then, not just be posted; if the decision has no or a wrong "
                 "Rechtsbehelfsbelehrung, the period is one year (§ 58 VwGO, § 66 SGG)")
    return Deadline("objection must arrive by", shifted,
                    "§ 70 VwGO / § 84 SGG / § 355 AO with § 41(2) VwVfG / § 37(2) SGB X / § 122(2) AO", tuple(notes))


def withdrawal(start: date, region: str = "DE") -> Deadline:
    """Widerruf of a distance contract: 14 days from receipt of the goods (services: from the contract).

    Sending the withdrawal in time is enough (§ 355(1) BGB).
    """
    end = shift_193(start + timedelta(days=14), region)
    return Deadline("withdrawal must be sent by", end, "§§ 355, 356 BGB, § 193 BGB", (
        "start is the day the goods arrived (for services or digital content: the day the contract was made)",
        "if you were never told about the right of withdrawal, it lasts 12 months and 14 days (§ 356(3) BGB)",
    ))


def third_werktag(year: int, month: int, region: str = "DE") -> date:
    d, count = date(year, month, 1), 0
    while True:
        if is_werktag(d, region):
            count += 1
            if count == 3:
                return d
        d += timedelta(days=1)


def tenancy_notice(delivery: date, region: str = "DE") -> tuple[Deadline, Deadline]:
    """A tenant's ordinary notice on a flat (§ 573c(1) BGB): received by the third Werktag of a month,
    the tenancy ends with the month after next. Returns (latest delivery date, end of tenancy).

    Saturdays count as Werktage here (BGH VIII ZR 206/04). Whether the deadline moves when the third
    Werktag is a Saturday is disputed (LG Berlin 65 S 395/16 says yes), so the safe date is returned.
    """
    cutoff = third_werktag(delivery.year, delivery.month, region)
    first = date(delivery.year, delivery.month, 1)
    if delivery > cutoff:
        first = add_months(first, 1)
        cutoff = third_werktag(first.year, first.month, region)
    end = last_day_of_month(add_months(first, 2))
    notes = ["the notice must be received by the landlord by this date, not just posted",
             "Saturdays count (BGH VIII ZR 206/04); if this date is a Saturday some courts allow the next working "
             "day, but do not rely on it",
             "a contract can give the tenant a shorter period, never a longer one (§ 573c(4) BGB)"]
    return (Deadline("notice must be received by", cutoff, "§ 573c(1) BGB", tuple(notes)),
            Deadline("tenancy ends on", end, "§ 573c(1) BGB"))


def employment_notice(delivery: date, probation: bool = False) -> Deadline:
    """An employee's statutory notice (§ 622 BGB): four weeks to the 15th or the end of a month; during
    agreed probation, two weeks to any day. Contracts and collective agreements may differ."""
    if probation:
        return Deadline("employment ends on", delivery + timedelta(days=14), "§ 622(3) BGB",
                        ("two weeks from the day after the employer receives the notice",))
    d = delivery + timedelta(days=28)
    end = date(d.year, d.month, 15) if d.day <= 15 else last_day_of_month(d)
    return Deadline("employment ends on", end, "§ 622(1) BGB", (
        "statutory minimum for employees; your contract or collective agreement may set a longer period, check it",
        "the employer must receive the signed paper letter; § 193 BGB does not extend notice periods",
    ))


def contract_notice(delivery: date, term_end: date | None = None, notice_months: int = 1) -> Deadline:
    """Cancelling a consumer contract (gym, mobile, streaming, insurance).

    Contracts made since 1 March 2022 run on indefinitely after the first term and can then be cancelled
    with one month's notice at any time (§ 309 No. 9 BGB). Before the first term ends, the contract's own
    notice period applies, and the contract ends with the term.
    """
    if term_end and delivery <= add_months(term_end, -notice_months):
        return Deadline("contract ends on", term_end, "contract terms; § 309 No. 9 BGB", (
            f"received at least {notice_months} month(s) before the end of the minimum term",))
    end = add_months(delivery, notice_months)
    notes = ["after the minimum term, contracts made since 1 March 2022 can be cancelled at any time with one "
             "month's notice; older contracts may still renew for up to a year"]
    if term_end and term_end > end:
        end = term_end
    return Deadline("contract ends on", end, "§ 309 No. 9 BGB; § 56(3) TKG for phone and internet", tuple(notes))


def data_access_reply(received: date, region: str = "DE") -> Deadline:
    """An answer to a GDPR access request is due within one month of receipt (Art. 12(3) GDPR)."""
    end = shift_193(add_months(received, 1), region)
    return Deadline("company must answer by", end, "Art. 12(3) GDPR", (
        "the company may extend by two more months for complex requests, but must tell you within the first month",
    ))
