from dataclasses import replace

from german_letters import Address, Letter, check, to_text
from german_letters.letter import SCHRIFTFORM, date_long, date_numeric

from .helpers import ME, THEM, d

BASE = Letter(ME, THEM, "Kündigung meines Vertrags", ("hiermit kündige ich meinen Vertrag.",), "Berlin", d("2026-11-23"))


def test_a_conventional_letter_has_no_warnings():
    assert check(BASE) == []


def test_dates():
    assert date_numeric(d("2026-03-08")) == "08.03.2026"
    assert date_long(d("2026-03-08")) == "8. März 2026"


def test_subject_must_not_have_a_label():
    assert any("Betreff" in w for w in check(replace(BASE, subject="Betreff: Kündigung")))


def test_first_word_after_the_salutation_is_lower_case():
    assert any("lower case" in w for w in check(replace(BASE, body=("Hiermit kündige ich.",))))
    assert check(replace(BASE, body=("Ihre Rechnung vom 1. März ist falsch.",))) == []  # polite form stays capitalised
    assert check(replace(BASE, body=("Kündigungen müssen schriftlich erfolgen.",))) == []  # nouns stay capitalised


def test_salutation_comma_and_closing_without_comma():
    assert any("salutation" in w for w in check(replace(BASE, salutation="Sehr geehrte Damen und Herren")))
    assert any("closing" in w for w in check(replace(BASE, closing="Mit freundlichen Grüßen,")))


def test_postcodes_and_missing_parts():
    bad = replace(BASE, recipient=Address("X GmbH", "", "1011", "Berlin"), subject="", body=())
    w = check(bad)
    assert any("no street" in x for x in w) and any("not five digits" in x for x in w)
    assert any("no subject" in x for x in w) and any("no text" in x for x in w)
    abroad = replace(BASE, recipient=Address("Firma", "Rue 1", "75001", "Paris", country="Frankreich"))
    assert check(abroad) == []


def test_schriftform_always_warns_to_sign_on_paper():
    assert any("sign it by hand" in w for w in check(replace(BASE, form=SCHRIFTFORM)))


def test_plain_text_layout():
    text = to_text(replace(BASE, references=(("Kundennummer", "123"),), enclosures=("Kopie", "Foto"),
                           delivery_note="Einschreiben", email="a@example.org"))
    lines = text.splitlines()
    assert lines[:3] == ["Alex Beispiel", "Musterstraße 12", "10115 Berlin"]
    assert "Einschreiben" in lines and "Berlin, 23.11.2026" in lines and "Kundennummer: 123" in lines
    assert "Anlagen" in lines and "- Foto" in lines and "E-Mail: a@example.org" in lines


def test_address_lines():
    a = Address("Amt", "Weg 1", "10115", "Berlin", extra="z. Hd. Frau Muster", country="Deutschland")
    assert a.lines() == ["Amt", "z. Hd. Frau Muster", "Weg 1", "10115 Berlin", "DEUTSCHLAND"]
