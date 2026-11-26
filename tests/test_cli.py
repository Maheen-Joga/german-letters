import json

import pytest

from german_letters.cli import main

from .helpers import EXAMPLES


def test_list(capsys):
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    assert out.count("\n") == 6 and "widerspruch-bescheid" in out and "Schriftform" in out


def test_show(capsys):
    assert main(["show", "kuendigung-arbeitsvertrag"]) == 0
    out = capsys.readouterr().out
    assert "§§ 622, 623 BGB" in out and "beginn: Start date" in out and "(optional)" in out and "arbeitsuchend" in out


@pytest.mark.parametrize("args, expected", [
    (["objection", "20.11.2026"], "objection must arrive by: Thu 24.12.2026"),
    (["objection", "2026-11-20", "--received", "2026-11-30"], "Wed 30.12.2026"),
    (["withdrawal", "2026-12-11"], "withdrawal must be sent by: Mon 28.12.2026"),
    (["tenancy", "2026-12-04"], "tenancy ends on: Wed 31.03.2027"),
    (["employment", "2026-11-03"], "employment ends on: Tue 15.12.2026"),
    (["employment", "2026-11-23", "--probation"], "Mon 07.12.2026"),
    (["contract", "2026-11-23", "--term-end", "2027-03-31"], "contract ends on: Wed 31.03.2027"),
    (["data-access", "2026-11-25", "--region", "BE"], "Mon 28.12.2026"),
])
def test_deadline(capsys, args, expected):
    assert main(["deadline", *args]) == 0
    out = capsys.readouterr().out
    assert expected in out and "Not legal advice" in out


def test_deadline_rejects_bad_dates():
    with pytest.raises(SystemExit) as e:
        main(["deadline", "objection", "31.02.2026"])
    assert e.value.code == 2


def test_write_example_with_html(tmp_path, capsys):
    html, text = tmp_path / "brief.html", tmp_path / "brief.txt"
    assert main(["write", str(EXAMPLES / "kuendigung-mietvertrag.json"), "--html", str(html), "--text", str(text)]) == 0
    out = capsys.readouterr().out
    assert "fristgerecht zum 28.02.2027" in out and "What it says, in English:" in out
    assert "notice must be received by: Thu 03.12.2026" in out and "! this letter needs Schriftform" in out
    assert "how to send: Print, sign by hand" in out
    assert html.read_text(encoding="utf-8").startswith("<!doctype html>") and "Hausverwaltung" in text.read_text(encoding="utf-8")


def test_every_example_writes(capsys):
    for f in sorted(EXAMPLES.glob("*.json")):
        assert main(["write", str(f), "-q"]) == 0, f.name


def test_free_letter_without_template(tmp_path, capsys):
    spec = {"sender": {"name": "A", "street": "S 1", "postcode": "10115", "city": "Berlin"},
            "recipient": {"name": "B", "street": "T 2", "postcode": "10117", "city": "Berlin"},
            "place": "Berlin", "date": "23.11.2026", "subject": "Anfrage", "body": ["ich habe eine Frage."]}
    f = tmp_path / "free.json"
    f.write_text(json.dumps(spec), encoding="utf-8")
    assert main(["write", str(f)]) == 0
    out = capsys.readouterr().out
    assert "Anfrage" in out and "Berlin, 23.11.2026" in out and "What it says" not in out


def test_write_reports_every_problem(tmp_path, capsys):
    f = tmp_path / "bad.json"
    f.write_text(json.dumps({"template": "widerruf", "sender": {"name": "A", "street": "S", "postcode": "1", "city": "B"},
                             "recipient": {"name": "B", "street": "T", "postcode": "10117", "city": "Berlin"},
                             "place": "Berlin", "date": "2026-11-23", "values": {"ware": "x"}}), encoding="utf-8")
    assert main(["write", str(f)]) == 2
    err = capsys.readouterr().err
    assert "missing bestellnummer" in err and "missing erhalten_am" in err


def test_write_bad_inputs(tmp_path, capsys):
    assert main(["write", str(tmp_path / "nope.json")]) == 2
    (tmp_path / "x.json").write_text("{not json")
    assert main(["write", str(tmp_path / "x.json")]) == 2
    (tmp_path / "y.json").write_text('{"place": "Berlin"}')
    assert main(["write", str(tmp_path / "y.json")]) == 2
    err = capsys.readouterr().err
    assert "cannot read" in err and "not valid JSON" in err and "missing sender" in err


def test_version(capsys):
    with pytest.raises(SystemExit):
        main(["--version"])
    assert "german-letters 0.1.0" in capsys.readouterr().out
