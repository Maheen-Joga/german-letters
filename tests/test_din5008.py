import re

from german_letters import build
from german_letters.din5008 import render_html

from .helpers import ME, THEM, d


def page():
    letter, _, _ = build("auskunft-dsgvo", ME, THEM, {"bekannt_als": "Kundennummer <1>"}, "Berlin", d("2026-11-23"),
                         email="a@example.org", enclosures=("Kopie Ausweis",))
    return render_html(letter)


def test_form_b_measurements():
    html = page()
    assert "top: 45mm; left: 20mm; width: 85mm; height: 45mm" in html
    assert ".m1 { top: 105mm; } .m2 { top: 210mm; } .hole { top: 148.5mm" in html
    assert "padding: 0 20mm 20mm 25mm" in html and "size: A4" in html


def test_content_is_escaped_and_complete():
    html = page()
    assert "Kundennummer &lt;1&gt;" in html and "<1>" not in html
    assert 'lang="de"' in html and "Auskunftsersuchen nach Art. 15 DSGVO" in html
    assert "<ul><li>eine Kopie dieser Daten (Art. 15 Abs. 3 DSGVO),</li>" in html
    assert "Alex Beispiel, Musterstraße 12, 10115 Berlin" in html  # return address line
    assert "<b>Anlage</b>" in html and "Mit freundlichen Grüßen" in html
    assert re.search(r"<dt>Datum</dt><dd>23\.11\.2026</dd>", html)


def test_self_contained():
    html = page()
    assert "http" not in html.replace("https://", "")  # no external fonts, scripts or images
    assert "<script" not in html
