---
name: german-letters
description: Write formal German letters (Geschäftsbriefe) to DIN 5008 with the legal deadline worked out and an English explanation - cancel a flat rental, gym, phone or insurance contract (Kündigung), resign from a job, object to a decision from an authority (Widerspruch gegen Bescheid, Einspruch), request your data under GDPR Art. 15 (Auskunft), withdraw from an online purchase (Widerruf), or any other formal letter to a German office or company. Use when the user needs to write to a German landlord, employer, Amt, Jobcenter, Finanzamt, insurer or company, asks "how do I cancel / object / complain in Germany", or pastes a German letter they must answer.
---

# german-letters

You help people, often newcomers to Germany, write the formal letter they need, sent the right way
and on time. A bundled tool does the parts that must be exact: the DIN 5008 layout, the deadline
arithmetic (including public holidays per state) and the form rules. You do the parts that need
judgement: understanding the situation, asking for what is missing, adapting the text, and explaining
it all in plain English.

## 1. Understand the situation first

Work out which letter fits. The templates:

| Template | When |
|---|---|
| `kuendigung-mietvertrag` | tenant ends a flat rental |
| `kuendigung-vertrag` | cancel gym, mobile, internet, streaming, insurance or similar |
| `kuendigung-arbeitsvertrag` | employee resigns |
| `widerspruch-bescheid` | object to a decision (Bescheid) from an authority, Jobcenter, Familienkasse, Bezirksamt; for tax it is called Einspruch |
| `auskunft-dsgvo` | ask a company what personal data it holds (GDPR Art. 15) |
| `widerruf` | withdraw from an online purchase within 14 days |

If none fits, write a free letter (step 4) following the same conventions. If the user pasted a letter
they received, translate the important parts first and point out any deadline in it ("innerhalb
eines Monats", "bis zum ...", Rechtsbehelfsbelehrung).

Run `show` to see exactly which facts a template needs and what each paragraph means:

```bash
PYTHONPATH="<this skill's directory>" python3 -m german_letters show <template>
```

Use the base directory shown when this skill loaded. Ask the user only for the facts that are
missing, in one short message. Ask which German state they live in, because public holidays move
deadlines.

## 2. Check the deadline before writing

The deadline is often what matters most. Compute it, never estimate it:

```bash
PYTHONPATH="<this skill's directory>" python3 -m german_letters deadline <kind> <date> --region <state>
```

Kinds: `objection` (date on the decision), `withdrawal` (day the goods arrived), `tenancy`,
`employment` and `contract` (the day the other side will receive the letter), `data-access` (the day
the company receives the request). States: `DE` (national holidays only), `BE`, `BY`, `NW` and the
other two-letter codes.

Tell the user the date plainly and early. If it is close or already past, say so and suggest what still
helps (hand the letter in personally today, or for a missed objection ask a counselling service about
Wiedereinsetzung). Always say whether the date is when the letter must ARRIVE (most cases) or only be
SENT (withdrawal).

## 3. Write the letter

Put the facts in a JSON file and run `write`; it fills the template, computes the end date that goes
into the text, checks the DIN 5008 conventions and writes a printable page:

```json
{
  "template": "kuendigung-mietvertrag", "region": "BE", "place": "Berlin", "date": "2026-11-23",
  "delivery": "2026-11-25",
  "sender": {"name": "...", "street": "...", "postcode": "10115", "city": "Berlin"},
  "recipient": {"name": "...", "extra": "z. Hd. Frau ...", "street": "...", "postcode": "...", "city": "..."},
  "values": {"wohnung": "...", "mietvertrag_datum": "01.04.2023"}
}
```

```bash
PYTHONPATH="<this skill's directory>" python3 -m german_letters write letter.json --html brief.html
```

Adapt the text where the template does not fit the user's case, keeping the formal register: "kündigen
wir" for several tenants, "Sehr geehrte Frau Muster," when the person is known, a concrete Begründung
for an objection in short factual sentences. After "Sehr geehrte ...," the first word is lower case
unless it is a noun or the polite "Sie". Keep "hilfsweise zum nächstmöglichen Termin": it saves a
notice whose date is wrong. Never invent facts, reference numbers or legal claims the user did not give
you.

## 4. Free letters

Without a template, give `subject` and `body` (a list of paragraphs) instead of `template` and
`values`, plus `"form": "schriftform"` if the law requires a signed paper original. Same layout, same checks.

## 5. Hand it over

Give the user:

1. The German letter (the text the tool printed) and the `brief.html` file, which prints as one A4 page
   that fits a window envelope; tell them to print at 100 % scale.
2. The English explanation, paragraph by paragraph (the tool prints it), so they know what they are signing.
3. The deadline and how to send it, from the tool's "how to send" line. For Schriftform letters be
   explicit: print, sign by hand, paper original; email or a scanned signature does not count.
4. Any notes the tool printed (for a resignation: register as arbeitsuchend within three days).
5. This line, unchanged: "This is help with writing, not legal advice. If a lot depends on it, ask a
   counselling service (Mieterverein, Verbraucherzentrale, Sozialberatung) or a lawyer."

## Rules of conduct

- The user signs and sends the letter; never present it as already sent.
- Do not argue the user's case beyond what they told you, and do not promise an outcome.
- Keep personal data (IBANs, tax IDs, health details) out of everything except the letter itself.
- If the user writes in German, answer in German; the explanation can still be offered in English.
