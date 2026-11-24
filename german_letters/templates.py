"""Letter templates: formal German text, an English explanation of every paragraph, the form the
law requires and how to send it.

Placeholders are written {name}. A paragraph whose optional placeholders are empty is left out; a
paragraph with a `fallback` uses it instead. Computed dates ({ende}) come from deadlines.py.
"""
from __future__ import annotations

import re
import string
from dataclasses import dataclass, field
from datetime import date, timedelta

from . import deadlines as dl
from .letter import FORMFREI, SCHRIFTFORM, TEXTFORM, Address, Letter, LetterError, date_numeric


@dataclass(frozen=True)
class Field:
    name: str
    question: str  # what to ask the user, in English
    required: bool = True
    example: str = ""


@dataclass(frozen=True)
class Paragraph:
    de: str
    en: str  # plain-English explanation of what the German says
    fallback: str = ""  # used when a placeholder in `de` has no value
    fallback_en: str = ""


@dataclass(frozen=True)
class Template:
    id: str
    title: str  # English
    title_de: str
    form: str
    send: str  # how to send it, in English
    basis: str
    subject: str
    paragraphs: tuple[Paragraph, ...]
    fields: tuple[Field, ...]
    deadline: str = ""  # name of the deadline rule, if any
    delivery_note: str = ""
    notes: tuple[str, ...] = field(default=())

    def field_names(self) -> list[str]:
        return [f.name for f in self.fields]


def _placeholders(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


TEMPLATES: dict[str, Template] = {}


def _add(t: Template) -> None:
    TEMPLATES[t.id] = t


_add(Template(
    id="kuendigung-mietvertrag", title="Cancel a flat rental (tenant)", title_de="Kündigung des Mietvertrags",
    form=SCHRIFTFORM, basis="§§ 568, 573c BGB", deadline="tenancy",
    send="Print, sign by hand (every tenant on the contract signs), and hand it over with a witness or send it by "
         "Einwurf-Einschreiben. Email, fax or WhatsApp do not end a tenancy.",
    delivery_note="Einwurf-Einschreiben",
    subject="Kündigung des Mietvertrags für die Wohnung {wohnung}",
    fields=(Field("wohnung", "Which flat? Street, house number and floor or flat number", example="Musterstraße 12, 3. OG links"),
            Field("mietvertrag_datum", "Date the rental contract was signed (DD.MM.YYYY)", example="01.04.2023"),
            Field("kaution_iban", "IBAN for returning the deposit (leave empty to skip)", required=False)),
    paragraphs=(
        Paragraph("hiermit kündige ich das Mietverhältnis über die oben genannte Wohnung (Mietvertrag vom "
                  "{mietvertrag_datum}) ordentlich und fristgerecht zum {ende}, hilfsweise zum nächstmöglichen Termin.",
                  "I give ordinary notice on the flat (contract dated {mietvertrag_datum}) effective {ende}, or the "
                  "earliest possible date if that one is wrong. The fallback protects you if the date is miscalculated."),
        Paragraph("Bitte bestätigen Sie mir den Eingang dieser Kündigung und das Ende des Mietverhältnisses schriftlich.",
                  "Please confirm in writing that you received this notice and when the tenancy ends."),
        Paragraph("Für die Übergabe der Wohnung und der Schlüssel schlage ich einen Termin in der letzten Woche des "
                  "Mietverhältnisses vor. Bitte teilen Sie mir mit, welcher Tag Ihnen passt.",
                  "I suggest handing over the flat and keys in the last week of the tenancy; tell me which day suits you."),
        Paragraph("Bitte überweisen Sie die Mietkaution nach Abrechnung auf folgendes Konto: {kaution_iban}",
                  "Please pay back the deposit, after settling accounts, to this account: {kaution_iban}"),
    ),
    notes=("Landlords may take up to about six months to settle the deposit; that is normal.",),
))

_add(Template(
    id="kuendigung-vertrag", title="Cancel a contract (gym, mobile, internet, streaming, insurance)",
    title_de="Kündigung eines Vertrags", form=TEXTFORM, basis="§ 309 Nos. 9 and 13, § 312k BGB; § 56 TKG",
    deadline="contract",
    send="Email or the provider's online cancellation button (§ 312k BGB) is enough for consumer contracts. Keep a "
         "copy and the confirmation. Use a letter by Einschreiben if the provider ignores you.",
    subject="Kündigung meines Vertrags, Kundennummer {kundennummer}",
    fields=(Field("vertrag", "What contract? Provider product or tariff name", example="Mitgliedschaft im Fitnessstudio"),
            Field("kundennummer", "Customer or contract number", example="123456")),
    paragraphs=(
        Paragraph("hiermit kündige ich meinen Vertrag ({vertrag}, Kundennummer {kundennummer}) fristgerecht zum "
                  "nächstmöglichen Zeitpunkt.",
                  "I cancel my contract ({vertrag}) at the earliest date the contract allows."),
        Paragraph("Bitte bestätigen Sie mir die Kündigung und das Vertragsende innerhalb von 14 Tagen in Textform.",
                  "Please confirm the cancellation and the end date within 14 days, by email or letter."),
        Paragraph("Einer Verlängerung des Vertrags widerspreche ich. Bitte kontaktieren Sie mich nicht, um mir "
                  "Angebote zur Weiterführung zu machen.",
                  "I object to any renewal, and please do not contact me with offers to stay."),
        Paragraph("Das erteilte SEPA-Lastschriftmandat widerrufe ich mit Wirkung zum Vertragsende.",
                  "I withdraw the direct-debit mandate from the end of the contract."),
    ),
))

_add(Template(
    id="kuendigung-arbeitsvertrag", title="Resign from a job (employee)", title_de="Kündigung des Arbeitsverhältnisses",
    form=SCHRIFTFORM, basis="§§ 622, 623 BGB", deadline="employment",
    send="Print, sign by hand and hand it to HR or your manager in person (ask them to sign a copy with the date), "
         "or send it by Einwurf-Einschreiben early enough. Email, PDF or a scanned signature are void (§ 623 BGB).",
    subject="Kündigung meines Arbeitsverhältnisses",
    fields=(Field("beginn", "Start date of the job (DD.MM.YYYY)", example="01.09.2024"),
            Field("personalnummer", "Personnel number (leave empty to skip)", required=False),
            Field("probezeit", "Are you still in the agreed probation period? yes or no", required=False, example="no")),
    paragraphs=(
        Paragraph("hiermit kündige ich mein seit dem {beginn} bestehendes Arbeitsverhältnis ordentlich und fristgerecht "
                  "zum {ende}, hilfsweise zum nächstmöglichen Termin.",
                  "I resign from my job, which began on {beginn}, effective {ende}, or the earliest possible date if "
                  "that one is wrong."),
        Paragraph("Bitte bestätigen Sie mir den Erhalt dieser Kündigung und das Beendigungsdatum schriftlich.",
                  "Please confirm in writing that you received this and the end date."),
        Paragraph("Ich bitte um ein qualifiziertes Arbeitszeugnis.",
                  "I ask for a detailed reference letter (you have a right to one, § 109 GewO)."),
        Paragraph("Für die gute Zusammenarbeit bedanke ich mich und wünsche Ihnen und dem Team alles Gute.",
                  "Thank you for working together; all the best to you and the team."),
    ),
    notes=("Register with the Agentur für Arbeit as 'arbeitsuchend' within three days of handing in your notice, "
           "or three months before the end if your notice period is longer (§ 38 SGB III); otherwise benefits can "
           "be cut. Resigning yourself can also mean a waiting period for unemployment benefit.",
           "Check your contract and any collective agreement: they often set a longer notice period than the "
           "statutory four weeks."),
))

_add(Template(
    id="widerspruch-bescheid", title="Object to a decision by an authority (Bescheid)",
    title_de="Widerspruch gegen einen Bescheid", form=SCHRIFTFORM,
    basis="§§ 68-70 VwGO, §§ 83-84 SGG", deadline="objection",
    send="Print, sign by hand and send it so that it ARRIVES before the deadline (Einwurf-Einschreiben, or hand it in "
         "and get a stamped copy). A normal email is usually not enough; fax is accepted by most authorities.",
    delivery_note="Einwurf-Einschreiben",
    subject="Widerspruch gegen den Bescheid vom {bescheid_datum}, Aktenzeichen {aktenzeichen}",
    fields=(Field("bescheid_datum", "Date printed on the decision (DD.MM.YYYY)", example="20.11.2026"),
            Field("aktenzeichen", "Reference number (Aktenzeichen, Geschäftszeichen or BG-Nummer)", example="123-45/2026"),
            Field("begruendung", "Why is the decision wrong? (leave empty to send reasons later)", required=False)),
    paragraphs=(
        Paragraph("hiermit lege ich gegen den oben genannten Bescheid vom {bescheid_datum} fristgerecht Widerspruch ein.",
                  "I formally object to the decision dated {bescheid_datum}, within the deadline."),
        Paragraph("Begründung: {begruendung}",
                  "My reasons: {begruendung}",
                  fallback="Die Begründung reiche ich nach. Zu diesem Zweck beantrage ich Einsicht in die Verwaltungsakte.",
                  fallback_en="I will send my reasons later, and I ask to see the case file. This keeps the deadline "
                              "even if you need time to understand the decision."),
        Paragraph("Bitte bestätigen Sie mir den Eingang dieses Widerspruchs.",
                  "Please confirm that you received this objection."),
    ),
    notes=("For a tax assessment (Steuerbescheid) the remedy is called Einspruch (§ 347 AO): same one-month deadline, "
           "write 'Einspruch' instead of 'Widerspruch'; it can also be filed through ELSTER.",
           "An objection usually does not stop the decision from taking effect; for Bürgergeld and tax decisions, "
           "ask the authority or a counselling service whether to apply for a suspension.",
           "Free help: Sozialberatung, Mieterverein, Verbraucherzentrale, or legal aid (Beratungshilfe) from the local court."),
))

_add(Template(
    id="auskunft-dsgvo", title="Ask a company what data it holds about you (GDPR Art. 15)",
    title_de="Auskunftsersuchen nach Art. 15 DSGVO", form=TEXTFORM, basis="Art. 12, 15 GDPR", deadline="data-access",
    send="Email to the company's data protection contact (see its privacy policy, 'Datenschutz') is enough. Keep the sent email.",
    subject="Auskunftsersuchen nach Art. 15 DSGVO",
    fields=(Field("bekannt_als", "How does the company know you? Customer number, email or username", example="Kundennummer 98765"),),
    paragraphs=(
        Paragraph("ich bitte Sie um Auskunft nach Art. 15 der Datenschutz-Grundverordnung (DSGVO), ob Sie "
                  "personenbezogene Daten über mich verarbeiten. Falls ja, bitte ich um:\n"
                  "- eine Kopie dieser Daten (Art. 15 Abs. 3 DSGVO),\n"
                  "- die Zwecke der Verarbeitung und die Kategorien der Daten,\n"
                  "- die Empfänger, insbesondere in Ländern außerhalb der EU,\n"
                  "- die geplante Speicherdauer,\n"
                  "- die Herkunft der Daten, soweit Sie sie nicht bei mir erhoben haben,\n"
                  "- Angaben zu automatisierten Entscheidungen einschließlich Profiling.",
                  "Under GDPR Art. 15 I ask whether you process my personal data and, if so, for a copy of it, the "
                  "purposes, who receives it (especially outside the EU), how long you keep it, where you got it and "
                  "whether you use automated decisions or profiling."),
        Paragraph("Bei Ihnen bin ich unter folgender Angabe bekannt: {bekannt_als}.",
                  "You know me as: {bekannt_als}. This helps them find you without asking for more ID."),
        Paragraph("Bitte antworten Sie innerhalb eines Monats nach Eingang dieses Schreibens (Art. 12 Abs. 3 DSGVO). "
                  "Die erste Kopie ist kostenlos.",
                  "Please answer within one month of receiving this; the first copy is free."),
    ),
    notes=("If the company does not answer in time, you can complain to the data protection authority of its state "
           "(in Berlin: the Berliner Beauftragte für Datenschutz und Informationsfreiheit).",),
))

_add(Template(
    id="widerruf", title="Withdraw from an online purchase (14 days)", title_de="Widerruf eines Fernabsatzvertrags",
    form=TEXTFORM, basis="§§ 355, 356, 357 BGB", deadline="withdrawal",
    send="Email is enough; sending it in time counts, even if it arrives later. Keep the sent email and the parcel receipt.",
    subject="Widerruf meiner Bestellung {bestellnummer}",
    fields=(Field("bestellnummer", "Order number", example="302-1234567"),
            Field("ware", "What did you buy?", example="Kopfhörer Modell X"),
            Field("bestellt_am", "Order date (DD.MM.YYYY)", example="05.12.2026"),
            Field("erhalten_am", "Date the goods arrived (DD.MM.YYYY)", example="11.12.2026")),
    paragraphs=(
        Paragraph("hiermit widerrufe ich den von mir abgeschlossenen Vertrag über den Kauf der folgenden Ware: {ware}, "
                  "bestellt am {bestellt_am}, erhalten am {erhalten_am}.",
                  "I withdraw from the purchase of {ware}, ordered on {bestellt_am} and received on {erhalten_am}. "
                  "This follows the official model withdrawal form."),
        Paragraph("Bitte erstatten Sie mir den Kaufpreis einschließlich der Kosten für die Standardlieferung "
                  "innerhalb von 14 Tagen über das ursprüngliche Zahlungsmittel.",
                  "Please refund the price, including standard delivery costs, within 14 days to the original payment method."),
        Paragraph("Bitte teilen Sie mir mit, wohin ich die Ware zurücksenden soll, sofern Sie mir kein Rücksendeetikett zusenden.",
                  "Tell me where to send the goods back if you do not send a return label."),
    ),
    notes=("The seller may make you pay return postage if it told you so before you bought.",),
))

FORM_LABEL = {SCHRIFTFORM: "Schriftform (signed paper original)", TEXTFORM: "Textform (email is fine)",
              FORMFREI: "no form required"}


def get(template_id: str) -> Template:
    try:
        return TEMPLATES[template_id]
    except KeyError:
        raise LetterError([f"unknown template {template_id!r}; choose from {sorted(TEMPLATES)}"]) from None


def _parse_date(text: str) -> date | None:
    for sep, order in (("-", "ymd"), (".", "dmy")):
        parts = text.strip().split(sep)
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            y, m, d = (parts if order == "ymd" else parts[::-1])
            try:
                return date(int(y), int(m), int(d))
            except ValueError:
                return None
    return None


def compute_deadline(t: Template, values: dict[str, str], day: date, delivery: date | None,
                     region: str) -> list[dl.Deadline]:
    """The deadlines that matter for this letter, given the letter date and the expected delivery date."""
    delivery = delivery or day + timedelta(days=2)
    if t.deadline == "tenancy":
        return list(dl.tenancy_notice(delivery, region))
    if t.deadline == "employment":
        return [dl.employment_notice(delivery, probation=values.get("probezeit", "").lower() in {"ja", "yes", "true", "1"})]
    if t.deadline == "objection":
        posted = _parse_date(values.get("bescheid_datum", ""))
        return [dl.objection(posted, None, region)] if posted else []
    if t.deadline == "withdrawal":
        got = _parse_date(values.get("erhalten_am", ""))
        return [dl.withdrawal(got, region)] if got else []
    if t.deadline == "contract":
        return [dl.contract_notice(delivery)]
    if t.deadline == "data-access":
        return [dl.data_access_reply(delivery, region)]
    return []


def build(template_id: str, sender: Address, recipient: Address, values: dict[str, str], place: str, day: date,
          delivery: date | None = None, region: str = "DE", **extra) -> tuple[Letter, list[dl.Deadline], list[str]]:
    """Fill a template. Returns the letter, its deadlines and English explanations (one per paragraph)."""
    t = get(template_id)
    values = {k: str(v).strip() for k, v in values.items() if v is not None}
    problems = [f"missing {f.name}: {f.question}" for f in t.fields if f.required and not values.get(f.name)]
    for f in t.fields:
        if f.name.endswith(("datum", "_am", "beginn")) and values.get(f.name) and not _parse_date(values[f.name]):
            problems.append(f"{f.name} {values[f.name]!r} is not a date like 20.11.2026")
    if problems:
        raise LetterError(problems)
    deadlines = compute_deadline(t, values, day, delivery, region)
    end = next((d for d in deadlines if d.label.endswith("ends on")), None)
    if end:
        values.setdefault("ende", date_numeric(end.when))
    body, explained = [], []
    for p in t.paragraphs:
        missing = [n for n in _placeholders(p.de) if not values.get(n)]
        if not missing:
            body.append(p.de.format(**values))
            explained.append(p.en.format(**values))
        elif p.fallback:
            body.append(p.fallback)
            explained.append(p.fallback_en)
    subject = t.subject.format_map(_Blank(values))
    refs = (("Personalnummer", values["personalnummer"]),) if values.get("personalnummer") else ()
    letter = Letter(sender=sender, recipient=recipient, subject=re.sub(r"\s+,", ",", subject).strip(" ,"),
                    body=tuple(body), place=place, day=day, form=t.form, references=refs,
                    delivery_note=extra.pop("delivery_note", t.delivery_note), notes=t.notes, **extra)
    return letter, deadlines, explained


class _Blank(dict):
    def __missing__(self, key: str) -> str:
        return ""
