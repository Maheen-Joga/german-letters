"""A formal German letter (Geschäftsbrief) and the checks a careful writer would make.

DIN 5008 conventions applied here: the subject line has no "Betreff:" label, the salutation
ends with a comma and the next paragraph starts in lower case, the closing has no comma,
dates are written "22.11.2026" or "22. November 2026", and German postcodes have five digits.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

MONTHS_DE = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September",
             "Oktober", "November", "Dezember")

# Form requirements, strictest first.
SCHRIFTFORM = "schriftform"  # paper, signed by hand (§ 126 BGB); email and fax are not enough
TEXTFORM = "textform"  # any readable text with the sender's name: email, fax, letter (§ 126b BGB)
FORMFREI = "formfrei"  # no form required
FORMS = (SCHRIFTFORM, TEXTFORM, FORMFREI)


class LetterError(ValueError):
    """The letter cannot be built; `problems` lists every reason."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


@dataclass(frozen=True)
class Address:
    name: str
    street: str
    postcode: str
    city: str
    extra: str = ""  # c/o, department or "z. Hd. Frau ..." line
    country: str = ""  # only for letters abroad, written in capitals in the last line

    def lines(self) -> list[str]:
        out = [self.name]
        if self.extra:
            out.append(self.extra)
        out += [self.street, f"{self.postcode} {self.city}".strip()]
        if self.country:
            out.append(self.country.upper())
        return [line for line in out if line]

    def one_line(self) -> str:
        return ", ".join([self.name, self.street, f"{self.postcode} {self.city}".strip()])


@dataclass(frozen=True)
class Letter:
    sender: Address
    recipient: Address
    subject: str
    body: tuple[str, ...]
    place: str
    day: date
    salutation: str = "Sehr geehrte Damen und Herren,"
    closing: str = "Mit freundlichen Grüßen"
    references: tuple[tuple[str, str], ...] = ()  # e.g. (("Kundennummer", "12345"),) shown under the subject
    enclosures: tuple[str, ...] = ()
    form: str = TEXTFORM
    delivery_note: str = ""  # e.g. "Einschreiben", printed above the recipient
    signer: str = ""  # defaults to the sender's name
    email: str = ""
    phone: str = ""
    notes: tuple[str, ...] = field(default=(), compare=False)  # English notes for the writer, never printed

    @property
    def signature_name(self) -> str:
        return self.signer or self.sender.name


def date_numeric(d: date) -> str:
    return f"{d.day:02d}.{d.month:02d}.{d.year}"


def date_long(d: date) -> str:
    return f"{d.day}. {MONTHS_DE[d.month - 1]} {d.year}"


POSTCODE = re.compile(r"^\d{5}$")
SUBJECT_LABEL = re.compile(r"^\s*(betreff|betr\.|subject)\s*:", re.I)


def check(letter: Letter) -> list[str]:
    """Return warnings in English. An empty list means the letter follows the conventions."""
    w: list[str] = []
    for role, a in (("sender", letter.sender), ("recipient", letter.recipient)):
        if not a.name.strip():
            w.append(f"{role} has no name")
        if not a.street.strip():
            w.append(f"{role} has no street and house number")
        if not a.country and not POSTCODE.match(a.postcode.strip()):
            w.append(f"{role} postcode {a.postcode!r} is not five digits; add a country if the address is abroad")
    if not letter.subject.strip():
        w.append("the letter has no subject line")
    elif SUBJECT_LABEL.match(letter.subject):
        w.append("DIN 5008 writes the subject without a 'Betreff:' label")
    if not letter.body or not any(p.strip() for p in letter.body):
        w.append("the letter has no text")
    if not letter.salutation.rstrip().endswith(","):
        w.append("the salutation should end with a comma")
    elif letter.body and _first_word(letter.body[0]) in MUST_BE_LOWER:
        w.append("after the salutation's comma the first paragraph starts in lower case "
                 f"('{_first_word(letter.body[0]).lower()} ...')")
    if letter.closing.rstrip().endswith(","):
        w.append("DIN 5008 writes the closing ('Mit freundlichen Grüßen') without a comma")
    if letter.form not in FORMS:
        w.append(f"unknown form {letter.form!r}")
    if letter.form == SCHRIFTFORM:
        w.append("this letter needs Schriftform: print it, sign it by hand and send the paper original; "
                 "email, fax or a scanned signature are not enough")
    return w


# Words that often open a letter and are not nouns, so after "Sehr geehrte ...," they are written in
# lower case. Nouns, names and the polite "Sie/Ihr" stay capitalised, so they are not listed.
MUST_BE_LOWER = frozenset({"Hiermit", "Ich", "Wir", "Mit", "Bitte", "Leider", "Vielen", "Gerne", "Gern", "Da",
                           "Wie", "Am", "Zum", "Zur", "Nach", "Unter", "In", "Im", "Auf", "Für", "Vor", "Wegen",
                           "Gegen", "Hierdurch", "Hiergegen", "Ihnen"} - {"Ihnen"})


def _first_word(paragraph: str) -> str:
    words = paragraph.split()
    return words[0].strip(",.;:") if words else ""


def to_text(letter: Letter) -> str:
    """Plain-text version, for email or for pasting into a word processor."""
    s = letter.sender
    lines = [*s.lines()]
    if letter.phone:
        lines.append(f"Telefon: {letter.phone}")
    if letter.email:
        lines.append(f"E-Mail: {letter.email}")
    lines += ["", *([letter.delivery_note] if letter.delivery_note else []), *letter.recipient.lines(), "",
              f"{letter.place}, {date_numeric(letter.day)}", "", letter.subject]
    lines += [f"{k}: {v}" for k, v in letter.references]
    lines += ["", letter.salutation, ""]
    for p in letter.body:
        lines += [p, ""]
    lines += [letter.closing, "", "", letter.signature_name]
    if letter.enclosures:
        lines += ["", "Anlage" + ("n" if len(letter.enclosures) > 1 else "")] + [f"- {e}" for e in letter.enclosures]
    return "\n".join(lines).rstrip() + "\n"
