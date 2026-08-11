# sis-deck-skill

A Claude Code skill that generates 1920×1080 HTML presentation decks in the **SIS** art
direction — the Swiss/editorial, monochrome, print-like system behind the SGN Investment
Summit deck.

`content.json` in, a single hand-editable `deck.html` out. Nine layout archetypes, every
style inline, no build step, no dependencies beyond Python 3.

## Install

Clone anywhere, then expose it to Claude Code as a skill:

```bash
ln -s "$PWD/sis-deck-skill" ~/.claude/skills/sis-deck
```

Ask for a deck in the SIS style, or invoke it directly with `/sis-deck`.

Used standalone, it is just a script — no install needed.

## Usage

```bash
python3 scripts/new_deck.py content.json --check
```

```bash
python3 scripts/new_deck.py content.json --out ./out
```

Then preview:

```bash
cd out && python3 -m http.server
```

Open `http://localhost:8000/deck.html`. Arrow keys / space navigate, there is a thumbnail
rail on the left, and **Print → Save as PDF** produces one page per slide at 1920×1080 with
no extra setup.

Options:

| Flag | Effect |
|---|---|
| `--check` | Validate and write nothing |
| `--out DIR` | Output directory (default `./out`) |
| `--assets-root DIR` | Where content asset paths resolve from (default `<content dir>/assets`) |
| `--fonts selfhosted` | Use `runtime/fonts/*.woff2` instead of Google Fonts |

The output directory is self-contained: `deck.html`, `deck-stage.js`, `styles.css`,
`tokens/`, and only the assets the content actually references.

## What's here

```
SKILL.md                    the skill prompt: art-direction rules, archetype catalogue, schema
templates/                  one HTML fragment per archetype + partials, with {{placeholders}}
schema/content.schema.json  field-by-field reference for content.json
scripts/new_deck.py         the generator and validator
scripts/verify_roundtrip.py proves the templates still reproduce the reference deck
examples/content.json       the SGN Investment Summit deck, as content
examples/ASSETS.md          where the sample images come from and why they aren't committed
reference/deck.html         the canonical deck this system was derived from
runtime/                    deck-stage.js, styles.css, tokens/ — copied into every deck
docs/TEMPLATING-REPORT.md   what in the design resisted templating, and why
tests/test_validator.py     29 guardrail tests
```

## The nine archetypes

`photo-cover` · `split-argument-photo` · `credibility` · `portrait-wall` ·
`category-matrix` · `data-three-zone` · `logo-wall-quotes` · `pricing-tiers` ·
`closing-photo-cta`

See `SKILL.md` for what each is for and how to choose between them.

## Content, briefly

```json
{
  "meta": {
    "event": "Your Summit",
    "date": "26 May 2026",
    "city": "Paris",
    "logos": { "lockupOnLight": "lockup-black.png", "lockupOnDark": "lockup-white.png" }
  },
  "slides": [
    {
      "archetype": "photo-cover",
      "label": "Cover",
      "photo": { "src": "photos/venue.jpg", "alt": "The main stage" },
      "kicker": "New for 2026",
      "headline": "Europe’s leading sport [[investment]] event",
      "lead": "One sentence that says what this is.",
      "factRail": ["[ Where deals begin ]", "26 May 2026", "Paris, France"]
    }
  ]
}
```

Three text conventions, because content is escaped and raw HTML is rejected:

- `[[run]]` — the silver text gradient. Exactly one per headline.
- `**bold**` — inline emphasis in body copy.
- `\n` — a hard line break.

## Art direction, non-negotiable

Monochrome. Sharp corners. 1px hairlines. No shadows, no icons, no emoji. Silver text
gradient on exactly one run per headline. Grayscale portraits, one-colour logos. Sober,
factual copy.

The generator enforces these as hard errors rather than trusting the caller — including
refusing to invent a speaker name, a logo or a statistic, and refusing to reuse the
rights-restricted SGN sample assets in another event's deck. `SKILL.md` states the full set.

## Tests

```bash
python3 tests/test_validator.py
```

```bash
python3 scripts/new_deck.py examples/content.json --out /tmp/sis --assets-root ../handoff-sis-deck/deck/assets && python3 scripts/verify_roundtrip.py /tmp/sis/deck.html reference/deck.html
```

The second one is the important one: it must print `identical`. That is the proof the
templates still reproduce `reference/deck.html` from `examples/content.json`, modulo one
allow-listed rule — see `docs/TEMPLATING-REPORT.md` §1 for what that rule is and why the
reference needs it.

## Licence

Proprietary — see [LICENSE](LICENSE). Internal SGN / SPORT[GEN] use, no redistribution.
The sample assets under `examples/assets/` are separately rights-restricted and are not
covered by it at all; see [examples/ASSETS.md](examples/ASSETS.md).
