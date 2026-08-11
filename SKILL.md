---
name: sis-deck
description: Generate a 1920×1080 HTML presentation deck in the SIS (SGN Investment Summit) art direction — Swiss/editorial, monochrome, print-like — from structured content. Use when asked to build, extend or restyle an event, sponsorship, investor or summit deck in the SIS / SGN / SPORT[GEN] house style, or when asked to turn speaker lists, sponsorship tiers, attendee demographics or media coverage into slides. Also use to add a slide to a deck this skill produced.
---

# SIS deck

Nine layout archetypes, one content schema, one generator. Output is a single
hand-editable `deck.html` with every style inline, plus the `<deck-stage>` runtime.
No build step.

## When to use this

- "Build the 2027 summit deck" / "make a sponsorship deck for X"
- "Add a speakers slide" / "swap the pricing tiers" on a deck this skill made
- Turning a speaker roster, attendee breakdown, media list or rate card into slides

## When not to use this

- A deck in someone else's brand. This art direction is specific and total; do not
  bend it toward another visual identity. Say so and stop.
- A document, one-pager or web page. This produces 16:9 slides only.

## Hard rules

These are not preferences. Break one and the deck is off-system.

1. **No colour accent, ever.** The only accent is the silver text gradient, on exactly
   one run per headline, written as `[[word]]` in content. Zero runs or two runs is an
   error, not a style choice.
2. **No radius, no shadow, no icon, no emoji.** Corners are `0`. Rules are 1px hairlines
   on `var(--line)`. Cards are a 1px border plus a `--bg-2`/`--panel-2` fill, nothing else.
3. **Every portrait is grayscale** (`grayscale(1) contrast(1.04)`) and **every logo is
   one colour** (`brightness(0); opacity:.82`). The single exemption is `keepColor: true`
   for a lockup whose licence forbids recolouring — document why when you use it.
   The cover photograph is the one image that keeps its colour, under a dark scrim.
4. **Never invent content.** Not a speaker name, not a job title, not an affiliation, not
   a logo, not a statistic, not a price. Missing data is an error to raise with the caller,
   not a gap to fill. The generator refuses to emit a slide with a missing field.
5. **The SGN sample assets are rights-restricted.** The portraits, media logos and event
   lockups in `examples/assets/` are cleared for SGN event marketing only. Every other
   deck supplies its own. The generator blocks them by name and by content hash; do not
   route around it.
6. **Copy is sober and factual.** No exclamation marks, no superlatives the client did not
   write, no marketing throat-clearing. Mono strings are uppercase (CSS does that) and
   often bracketed: `[ Where deals begin ]`, `[01]`.
7. **Layout is fixed.** Content slides: 144px side margins, 88px running banner,
   absolutely-positioned children inside a 1920×1080 stage. Nothing below 10px type, and
   nothing below 24px for anything a room must read from the back.
8. **Nine archetypes is the vocabulary.** If content does not fit one, say so and discuss
   it — do not improvise a tenth layout inline.

## The archetypes

| Archetype | Use it for | Wants |
|---|---|---|
| `photo-cover` | Slide 1 only. Sets the event. | One strong photograph, a headline, one lead sentence, three facts |
| `split-argument-photo` | The "why we exist" slide. An argument that needs a proof photo beside it. | 1–2 paragraphs, up to 4 stats, two meta pairs, one insert photo |
| `credibility` | Parent brand / track record. "Brought to you by". | A thumbnail row of names, a parent lockup, 2 paragraphs, 1–3 huge figures |
| `portrait-wall` | A roster. Speakers, investors, the committee. | 10–15 people with name, role, org, portrait. Auto-numbered `[01]`… |
| `category-matrix` | "Who's in the room" — named organisations grouped by kind. | 6 categories × 7–8 names reads best. Optional `(qualifier)` per name |
| `data-three-zone` | Audience demographics. Three unrelated cuts of the same population. | A stat rail, percentage bars, and one stacked share bar summing to 100 |
| `logo-wall-quotes` | Media presence, partners, or press. | Logos with per-logo optical caps, plus 4 short pull quotes with thumbs |
| `pricing-tiers` | A rate card. Sponsorship or ticket packages. | 2–4 tiers low to high, price, category, inclusions, benefit bullets |
| `closing-photo-cta` | The last slide. One venue photograph and the ask. | A headline, a lead ending in the CTA, one photo, two captions |

Choosing between them:

- A list of **people** → `portrait-wall`. A list of **organisations** → `category-matrix`.
  A list of **brands with marks** → `logo-wall-quotes`.
- Numbers that are **counts** → the stat rail in `data-three-zone` or `split-argument-photo`.
  Numbers that are **shares of a whole** → the bars or share bar in `data-three-zone`.
- One claim that needs **evidence** → `split-argument-photo`. One claim that needs
  **provenance** → `credibility`.
- `photo-cover` first, `closing-photo-cta` last, exactly once each.

## Content schema

`content.json`:

```json
{
  "meta": {
    "event": "…", "date": "25 May 2027", "city": "Paris",
    "logos": { "lockupOnLight": "lockup-black.png", "lockupOnDark": "lockup-white.png" }
  },
  "slides": [ { "archetype": "photo-cover", "label": "Cover", "…": "…" } ]
}
```

- Asset paths are relative to the assets root (default `<content dir>/assets`).
  Images are `"path.jpg"` or `{src, alt, …}`; `alt` is required in object form.
- `label` names the slide in the thumbnail rail and must be unique.
- Text conventions: `[[silver]]` in headlines, `**bold**` in body copy, `\n` for a
  line break. Everything else is escaped — **raw HTML in content is rejected**.
- Per-image crop controls (`objectPosition`, `scale` + `transformOrigin`) exist because
  head position in a photograph is not derivable from content. Use them; they are how the
  reference deck gets its portraits right.
- Logo entries require `maxHeight` and `maxWidth`. Set them by eye, per logo.

Full field-by-field reference: `schema/content.schema.json`.

Two worked examples, both covering all nine archetypes:

- `examples/sis-2027.json` — **the live deck.** SGN Investment Summit, 25 May 2027, Paris.
  Copy this to start a new deck, and edit this one for SIS itself.
- `examples/content.json` — the reference deck as authored (dated 26 May 2026, the
  originally planned date). It exists only to prove the templates still reproduce
  `reference/deck.html`. Do not edit it.

**SIS 2027 is the first edition** — the summit did not run in 2026. Where a slide mentions a
2026 event it means the **SPORT[GEN] Summit**, which did: slide 3's figures and slide 4's
speaker roster are SPORT[GEN] track record. Never relabel them as a past SIS edition, and
never present SPORT[GEN] speakers as confirmed for SIS.

## Running it

```bash
python3 scripts/new_deck.py content.json --out ./out
```

```bash
python3 scripts/new_deck.py content.json --check
```

- `--check` validates and writes nothing. Run it first; every guardrail above is a hard
  error with the offending field path (`slides[3].people[2].org`).
- `--assets-root DIR` if assets do not live next to the content file.
- `--fonts selfhosted` swaps Google Fonts for `runtime/fonts/*.woff2` (fails loudly if a
  binary is missing rather than falling back to a system sans).
- Preview: `cd out && python3 -m http.server`, open `deck.html`. Arrows navigate;
  Print → Save as PDF gives one page per slide at 1920×1080.

Regression check after any change to templates or generator:

```bash
python3 tests/test_validator.py && python3 scripts/new_deck.py examples/content.json --out /tmp/sis && python3 scripts/verify_roundtrip.py /tmp/sis/deck.html reference/deck.html
```

`verify_roundtrip.py` must report `identical` — that is the proof the templates still
reproduce the reference deck.

## Working on a generated deck by hand

Generated decks are meant to be edited directly: every style is inline and each slide is a
self-contained `<section>`, so a slide survives copy/paste between files. When you hand-edit,
the rules above still apply — and prefer changing `content.json` and regenerating, so the
deck and its source do not drift.

Two things not to touch in a generated deck: `deck-stage.js` (the shell) and the
`deck-stage>section{font-family:var(--font-body)}` rule in the head, which is what makes
Archivo actually apply. See `docs/TEMPLATING-REPORT.md`.
