import pytest

from german_letters import TEMPLATES, LetterError, build, check
from german_letters.letter import SCHRIFTFORM, TEXTFORM
from german_letters.templates import _placeholders, get

from .helpers import ME, THEM, d


def make(tid, values, day="2026-11-23", **kw):
    return build(tid, ME, THEM, values, "Berlin", d(day), **kw)


def test_every_template_is_complete():
    for t in TEMPLATES.values():
        assert t.title and t.title_de and t.send and t.basis and t.paragraphs
        names = set(t.field_names()) | {"ende"}
        for p in t.paragraphs:
            assert p.en and _placeholders(p.de) <= names, (t.id, _placeholders(p.de) - names)
            assert _placeholders(p.en) <= _placeholders(p.de) | names
        assert _placeholders(t.subject) <= names
        assert t.paragraphs[0].de[0].islower(), f"{t.id}: first paragraph must start in lower case after the salutation"


def test_tenancy_letter_fills_the_end_date():
    letter, deadlines, explained = make("kuendigung-mietvertrag", {"wohnung": "Musterstraße 12, 3. OG",
                                                                   "mietvertrag_datum": "01.04.2023"})
    assert "fristgerecht zum 28.02.2027" in letter.body[0] and "28.02.2027" in explained[0]
    assert [x.label for x in deadlines] == ["notice must be received by", "tenancy ends on"]
    assert letter.form == SCHRIFTFORM and letter.delivery_note == "Einwurf-Einschreiben"
    assert len(letter.body) == 3  # deposit paragraph skipped without an IBAN


def test_optional_paragraph_appears_with_its_value():
    letter, _, _ = make("kuendigung-mietvertrag", {"wohnung": "W", "mietvertrag_datum": "01.04.2023",
                                                   "kaution_iban": "DE00 1234"})
    assert letter.body[-1].endswith("DE00 1234")


def test_delivery_date_changes_the_end_date():
    v = {"wohnung": "W", "mietvertrag_datum": "01.04.2023"}
    early, _, _ = make("kuendigung-mietvertrag", v, day="2026-11-30", delivery=d("2026-12-02"))
    late, _, _ = make("kuendigung-mietvertrag", v, day="2026-11-30", delivery=d("2026-12-04"))
    assert "28.02.2027" in early.body[0] and "31.03.2027" in late.body[0]


def test_objection_uses_fallback_without_reasons():
    letter, deadlines, explained = make("widerspruch-bescheid", {"bescheid_datum": "20.11.2026", "aktenzeichen": "A-1"})
    assert letter.subject == "Widerspruch gegen den Bescheid vom 20.11.2026, Aktenzeichen A-1"
    assert "Verwaltungsakte" in letter.body[1] and "case file" in explained[1]
    assert deadlines[0].when == d("2026-12-24")


def test_objection_with_reasons():
    letter, _, _ = make("widerspruch-bescheid", {"bescheid_datum": "20.11.2026", "aktenzeichen": "A-1",
                                                 "begruendung": "Mein Einkommen wurde doppelt angerechnet."})
    assert letter.body[1] == "Begründung: Mein Einkommen wurde doppelt angerechnet."


def test_resignation_with_probation_and_personnel_number():
    letter, deadlines, _ = make("kuendigung-arbeitsvertrag", {"beginn": "01.09.2026", "probezeit": "yes",
                                                              "personalnummer": "4711"}, delivery=d("2026-11-23"))
    assert deadlines[0].when == d("2026-12-07") and "07.12.2026" in letter.body[0]
    assert letter.references == (("Personalnummer", "4711"),)


def test_data_access_and_withdrawal_are_textform():
    letter, deadlines, _ = make("auskunft-dsgvo", {"bekannt_als": "Kundennummer 1"})
    assert letter.form == TEXTFORM and "- eine Kopie dieser Daten" in letter.body[0]
    letter, deadlines, _ = make("widerruf", {"bestellnummer": "1", "ware": "Kopfhörer", "bestellt_am": "05.12.2026",
                                             "erhalten_am": "11.12.2026"})
    assert deadlines[0].when == d("2026-12-28") and letter.subject == "Widerruf meiner Bestellung 1"


def test_every_built_letter_passes_the_conventions_check():
    samples = {
        "kuendigung-mietvertrag": {"wohnung": "W", "mietvertrag_datum": "01.04.2023"},
        "kuendigung-vertrag": {"vertrag": "Fitness", "kundennummer": "1"},
        "kuendigung-arbeitsvertrag": {"beginn": "01.09.2024"},
        "widerspruch-bescheid": {"bescheid_datum": "20.11.2026", "aktenzeichen": "A"},
        "auskunft-dsgvo": {"bekannt_als": "x"},
        "widerruf": {"bestellnummer": "1", "ware": "x", "bestellt_am": "01.12.2026", "erhalten_am": "03.12.2026"},
    }
    assert set(samples) == set(TEMPLATES)
    for tid, values in samples.items():
        letter, _, _ = make(tid, values)
        assert [w for w in check(letter) if "Schriftform" not in w] == [], tid


def test_missing_and_malformed_values_are_all_reported():
    with pytest.raises(LetterError) as e:
        make("widerruf", {"ware": "x", "bestellt_am": "yesterday", "erhalten_am": "31.02.2026"})
    problems = e.value.problems
    assert any("missing bestellnummer" in p for p in problems)
    assert any("bestellt_am" in p for p in problems) and any("erhalten_am" in p for p in problems)


def test_unknown_template():
    with pytest.raises(LetterError):
        get("kuendigung-ehe")
