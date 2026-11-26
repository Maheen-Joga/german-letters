"""Command line: german-letters list | show | deadline | write"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from . import __version__
from . import deadlines as dl
from .din5008 import render_html
from .holidays import REGIONS
from .letter import Address, Letter, LetterError, check, to_text
from .templates import FORM_LABEL, TEMPLATES, build, get

EXIT_OK, EXIT_INPUT = 0, 2
DISCLAIMER = "Not legal advice. For anything with serious consequences, ask a counselling service or a lawyer."


def _date(text: str) -> date:
    text = text.strip()
    try:
        if "." in text:
            d, m, y = text.split(".")
            return date(int(y), int(m), int(d))
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a date like 2026-11-23 or 23.11.2026") from None


def cmd_list(_: argparse.Namespace) -> int:
    width = max(len(t) for t in TEMPLATES)
    for t in TEMPLATES.values():
        print(f"{t.id:<{width}}  {t.title}  [{FORM_LABEL[t.form]}]")
    return EXIT_OK


def cmd_show(args: argparse.Namespace) -> int:
    t = get(args.template)
    print(f"{t.title_de}: {t.title}")
    print(f"Form: {FORM_LABEL[t.form]}   Basis: {t.basis}")
    print(f"How to send: {t.send}\n\nFields:")
    for f in t.fields:
        flag = "" if f.required else " (optional)"
        eg = f'  e.g. "{f.example}"' if f.example else ""
        print(f"  {f.name}{flag}: {f.question}{eg}")
    print("\nWhat each paragraph says:")
    for i, p in enumerate(t.paragraphs, 1):
        print(f"  {i}. {p.en}")
    for n in t.notes:
        print(f"\nNote: {n}")
    return EXIT_OK


def _print_deadlines(items: list[dl.Deadline]) -> None:
    for d in items:
        print(f"{d.label}: {d.when.strftime('%a %d.%m.%Y')}  ({d.basis})")
        for n in d.notes:
            print(f"  - {n}")


def cmd_deadline(args: argparse.Namespace) -> int:
    kind, when, region = args.kind, args.date, args.region
    if kind == "objection":
        items = [dl.objection(when, args.received, region)]
    elif kind == "withdrawal":
        items = [dl.withdrawal(when, region)]
    elif kind == "tenancy":
        items = list(dl.tenancy_notice(when, region))
    elif kind == "employment":
        items = [dl.employment_notice(when, args.probation)]
    elif kind == "contract":
        items = [dl.contract_notice(when, args.term_end)]
    else:
        items = [dl.data_access_reply(when, region)]
    _print_deadlines(items)
    print(DISCLAIMER)
    return EXIT_OK


def _address(data: dict, role: str) -> Address:
    try:
        return Address(**{k: str(v) for k, v in data.items()})
    except TypeError as e:
        raise LetterError([f"{role}: {e}"]) from None


def load_letter(spec: dict) -> tuple[Letter, list[dl.Deadline], list[str]]:
    """Build a letter from a JSON spec: a template with values, or a free letter with subject and body."""
    missing = [k for k in ("sender", "recipient", "place", "date") if k not in spec]
    if missing:
        raise LetterError([f"missing {k}" for k in missing])
    sender, recipient = _address(spec["sender"], "sender"), _address(spec["recipient"], "recipient")
    day = _date(spec["date"])
    extra = {k: spec[k] for k in ("email", "phone", "signer", "salutation", "closing") if spec.get(k)}
    if spec.get("enclosures"):
        extra["enclosures"] = tuple(spec["enclosures"])
    if spec.get("delivery_note") is not None:
        extra["delivery_note"] = spec["delivery_note"]
    if spec.get("template"):
        delivery = _date(spec["delivery"]) if spec.get("delivery") else None
        return build(spec["template"], sender, recipient, spec.get("values", {}), spec["place"], day,
                     delivery=delivery, region=spec.get("region", "DE"), **extra)
    if not spec.get("subject") or not spec.get("body"):
        raise LetterError(["a letter without a template needs a subject and a body (a list of paragraphs)"])
    letter = Letter(sender=sender, recipient=recipient, subject=spec["subject"], body=tuple(spec["body"]),
                    place=spec["place"], day=day, form=spec.get("form", "textform"), **extra)
    return letter, [], []


def cmd_write(args: argparse.Namespace) -> int:
    try:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        letter, deadlines, explained = load_letter(spec)
    except OSError as e:
        print(f"error: cannot read {args.spec}: {e.strerror}", file=sys.stderr)
        return EXIT_INPUT
    except json.JSONDecodeError as e:
        print(f"error: {args.spec} is not valid JSON: {e.msg} (line {e.lineno})", file=sys.stderr)
        return EXIT_INPUT
    except (LetterError, argparse.ArgumentTypeError) as e:
        problems = e.problems if isinstance(e, LetterError) else [str(e)]
        print("error: the letter cannot be written", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return EXIT_INPUT
    if args.html:
        Path(args.html).write_text(render_html(letter), encoding="utf-8")
        print(f"wrote {args.html} (open it in a browser and print to PDF at 100 % scale)", file=sys.stderr)
    text = to_text(letter)
    if args.text:
        Path(args.text).write_text(text, encoding="utf-8")
    if not args.quiet:
        print(text)
    if explained:
        print("What it says, in English:")
        for i, line in enumerate(explained, 1):
            print(f"  {i}. {line}")
        print()
    if deadlines:
        _print_deadlines(deadlines)
        print()
    for w in check(letter):
        print(f"! {w}")
    for n in letter.notes:
        print(f"note: {n}")
    if spec.get("template"):
        print(f"how to send: {get(spec['template']).send}")
    print(DISCLAIMER)
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="german-letters", description="Formal German letters to DIN 5008, with the "
                                "deadlines worked out and an English explanation. " + DISCLAIMER)
    p.add_argument("--version", action="version", version=f"german-letters {__version__}")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list the letter templates").set_defaults(func=cmd_list)
    s = sub.add_parser("show", help="fields, form and how to send a template")
    s.add_argument("template", choices=sorted(TEMPLATES))
    s.set_defaults(func=cmd_show)
    d = sub.add_parser("deadline", help="work out a deadline")
    d.add_argument("kind", choices=("objection", "withdrawal", "tenancy", "employment", "contract", "data-access"))
    d.add_argument("date", type=_date, help="objection: date on the decision; withdrawal: day the goods arrived; "
                   "tenancy, employment, contract, data-access: day the letter will be received")
    d.add_argument("--received", type=_date, help="objection: the day the decision actually arrived, if later")
    d.add_argument("--term-end", type=_date, help="contract: end of the minimum term")
    d.add_argument("--probation", action="store_true", help="employment: still in the agreed probation period")
    d.add_argument("--region", choices=REGIONS, default="DE", help="state for public holidays (default: DE, national only)")
    d.set_defaults(func=cmd_deadline)
    w = sub.add_parser("write", help="write a letter from a JSON file")
    w.add_argument("spec", help="JSON file: sender, recipient, place, date, and a template with values or a subject and body")
    w.add_argument("--html", metavar="FILE", help="also write a DIN 5008 page to print or save as PDF")
    w.add_argument("--text", metavar="FILE", help="also write the plain text")
    w.add_argument("--quiet", "-q", action="store_true", help="do not print the letter text")
    w.set_defaults(func=cmd_write)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except LetterError as e:
        print(f"error: {e}", file=sys.stderr)
        return EXIT_INPUT
