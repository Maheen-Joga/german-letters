"""Render a letter as a printable A4 page laid out to DIN 5008 Form B.

Measurements (Form B): the address field starts 45 mm from the top and 20 mm from the left and is
85 x 45 mm: a 17.7 mm zone for the return address and delivery notes, then 27.3 mm for the
recipient, so it shows in the window of a DL envelope. Fold marks sit at 105 mm and 210 mm, the
punch mark at 148.5 mm. Text runs from 25 mm on the left to 20 mm from the right edge. The
information block with the date sits at 125 mm from the left. The output is one self-contained HTML
file; open it in a browser and print to PDF at 100 % scale with no headers or footers.
"""
from __future__ import annotations

from html import escape

from .letter import Letter, date_numeric

CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #e9e9e6; }
body { font: 11pt/1.35 Arial, "Helvetica Neue", Helvetica, "Liberation Sans", sans-serif; color: #111; }
.page { position: relative; width: 210mm; min-height: 297mm; margin: 10mm auto; background: #fff;
        padding: 0 20mm 20mm 25mm; box-shadow: 0 1px 6px rgba(0,0,0,.15); }
.head { position: absolute; top: 18mm; left: 25mm; right: 20mm; font-size: 9pt; line-height: 1.3; color: #333; }
.head b { font-size: 13pt; color: #111; display: block; margin-bottom: 1mm; }
.addr { position: absolute; top: 45mm; left: 20mm; width: 85mm; height: 45mm; }
.zone { height: 17.7mm; display: flex; flex-direction: column; justify-content: flex-end; font-size: 8pt; line-height: 1.2; }
.zone .ret { text-decoration: underline; text-decoration-thickness: .5pt; margin-bottom: 1mm; }
.recipient { height: 27.3mm; padding-left: 5mm; }
.recipient div, .zone div { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.zone div { padding-left: 5mm; }
.info { position: absolute; top: 50mm; left: 125mm; width: 75mm; font-size: 9pt; line-height: 1.35; }
.info dt { color: #555; }
.info dd { margin: 0 0 1.5mm; }
.text { padding-top: 98.5mm; }
.subject { font-weight: bold; margin: 0 0 1mm; }
.refs { margin: 0 0 8.5mm; font-size: 10pt; }
.text p { margin: 0 0 4.2mm; }
.text ul { margin: -2.5mm 0 4.2mm; padding-left: 6mm; }
.sign { margin-top: 4.2mm; }
.sign .space { height: 14mm; }
.encl { margin-top: 8mm; font-size: 10pt; }
.mark { position: absolute; left: 4mm; width: 6mm; border-top: .3pt solid #888; }
.m1 { top: 105mm; } .m2 { top: 210mm; } .hole { top: 148.5mm; width: 8mm; }
@media print { html, body { background: #fff; } .page { margin: 0; box-shadow: none; } }
"""


def _paragraph(text: str) -> str:
    """Lines starting with '- ' become a bulleted list."""
    lines = text.split("\n")
    head = [ln for ln in lines if not ln.startswith("- ")]
    items = [ln[2:] for ln in lines if ln.startswith("- ")]
    out = f"<p>{escape(' '.join(head))}</p>" if head else ""
    if items:
        out += "<ul>" + "".join(f"<li>{escape(i)}</li>" for i in items) + "</ul>"
    return out


def render_html(letter: Letter, title: str = "") -> str:
    s, r = letter.sender, letter.recipient
    head = f'<div class="head"><b>{escape(s.name)}</b>{escape(s.street)} · {escape(s.postcode)} {escape(s.city)}</div>'
    zone = [f'<div class="ret">{escape(s.one_line())}</div>']
    if letter.delivery_note:
        zone.append(f"<div>{escape(letter.delivery_note)}</div>")
    recipient = "".join(f"<div>{escape(line)}</div>" for line in r.lines())
    info = [("Datum", date_numeric(letter.day))]
    if letter.phone:
        info.insert(0, ("Telefon", letter.phone))
    if letter.email:
        info.insert(0, ("E-Mail", letter.email))
    info_html = "".join(f"<dt>{escape(k)}</dt><dd>{escape(v)}</dd>" for k, v in info)
    refs = "".join(f"<div>{escape(k)}: {escape(v)}</div>" for k, v in letter.references)
    body = "".join(_paragraph(p) for p in letter.body)
    encl = ""
    if letter.enclosures:
        label = "Anlagen" if len(letter.enclosures) > 1 else "Anlage"
        encl = f'<div class="encl"><b>{label}</b>' + "".join(f"<div>{escape(e)}</div>" for e in letter.enclosures) + "</div>"
    return f"""<!doctype html>
<html lang="de">
<head><meta charset="utf-8"><title>{escape(title or letter.subject)}</title><style>{CSS}</style></head>
<body><div class="page">
<span class="mark m1"></span><span class="mark hole"></span><span class="mark m2"></span>
{head}
<div class="addr"><div class="zone">{''.join(zone)}</div><div class="recipient">{recipient}</div></div>
<dl class="info">{info_html}</dl>
<div class="text">
<p class="subject">{escape(letter.subject)}</p>
<div class="refs">{refs}</div>
<p>{escape(letter.salutation)}</p>
{body}
<div class="sign">{escape(letter.closing)}<div class="space"></div>{escape(letter.signature_name)}</div>
{encl}
</div>
</div></body>
</html>
"""
