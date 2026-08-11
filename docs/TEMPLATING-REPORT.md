# What resisted templating, and why

Notes from deriving the nine archetype templates from `reference/deck.html`. The round-trip
is exact — `verify_roundtrip.py` reports 1680 of 1680 tokens identical — so nothing here
was papered over. These are the places where the design carries decisions that content
cannot express, and what the schema does about each.

## 1. The reference deck never applies Archivo

Not a templating problem — a defect in the design bundle, found while verifying it.

`deck-stage.js:158` sets `font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue",
Helvetica, Arial, sans-serif` on `:host`. Slides are slotted light-DOM children, so they
inherit through the `<slot>` from the shadow host — and nothing in `deck.html`, `styles.css`
or `tokens/` ever applies `var(--font-body)` to them. Verified in the browser:
`getComputedStyle(h1).fontFamily` is the `-apple-system` stack, and all 18 Archivo faces
report `status: "unloaded"`. The self-contained `reference/…(offline).html` has the same
hole (`body { font-family: -apple-system, BlinkMacSystemFont, sans-serif }`).

So every non-mono word in the reference — all headlines, all body copy, every stat figure —
renders in the system sans. IBM Plex Mono is unaffected because it is set inline in 137
places.

Setting it on `body` does not fix it: slotted elements inherit from the slot, not from their
light-DOM parent. Generated decks therefore add one document-level rule to the head:

```css
deck-stage>section{font-family:var(--font-body)}
```

This is the **only** intentional difference between generated output and the reference, and
it is the one thing `verify_roundtrip.py` allow-lists.

### Consequence: three blocks rewrap

Archivo is wider than SF Pro at display sizes, so fixing the font changes composition on
three slides. Measured, generated vs reference:

| Slide | Element | Reference | With Archivo |
|---|---|---|---|
| 1 Cover | `h1` 120px, `max-width:1480px` | 233px — 2 lines | 335px — **3 lines** |
| 3 Brought to you by | `h2` 64px in the 0.86fr column | 126px — 2 lines | 182px — **3 lines** |
| 9 Roland-Garros | lead `p` 24px, `max-width:1240px` | 36px — 1 line | 72px — **2 lines** |

Nothing breaks: no text is clipped, nothing lands outside the 1920×1080 stage, and both
decks still print to 9 pages. The cover's `margin:auto 0 0` absorbs the third line upward,
slide 3's `margin-top:auto` on the parent lockup absorbs it downward, and slide 9's photo is
`flex:1` so it simply gets shorter. Two thumbnail captions on slide 3 ("Kameryn Stanhope",
"Richard Heaselgrave") now wrap to two lines, which puts their org lines one step out of
alignment with their neighbours'.

Left as-is deliberately: the brief says fix nothing in the design, report it. If the 2-line
cover is wanted back, the lever is `headlineSize` or a shorter headline, not a font change.

## 2. Hand-tuned portrait crops

8 of the reference deck's 25 portraits carry a bespoke `object-position`, and most of those
also a `transform: scale(1.08–1.83)` with a matching `transform-origin` — for example
`object-position:30% 8%; transform:scale(1.83); transform-origin:30% 10%` on one thumbnail.

Where a face sits in a frame is a property of the photograph, not of the content. There is
no formula, and guessing produces decapitated headshots. Exposed as optional per-image
`objectPosition` / `scale` / `transformOrigin`, with `scale` requiring `transformOrigin` so
a half-specified crop cannot ship.

## 3. Per-logo optical caps

All 19 media logos have individually chosen `max-height` (40–74px) and `max-width`
(120–360px). A wordmark like *La Gazzetta dello Sport* needs 360px of width and only 42px of
height; *M6* needs 120px and 74px. Normalising by height, area or bounding box all read
badly, because optical weight depends on the mark's internal density.

No default is offered: `maxHeight` and `maxWidth` are **required** on every logo, and the
generator errors without them rather than picking a number that will look wrong.

## 4. One logo keeps its colour

Canal+ is rendered without `filter: brightness(0)` — the one exception to one-colour
lockups in the whole deck. Modelled as an explicit opt-in (`keepColor: true`) rather than a
special case in the template, so the exemption is visible in content and has to be a
decision. Everything else is flattened to black at 82% opacity.

## 5. "One word" is really "one run"

README §3 says the silver gradient goes on "exactly one word per headline". The deck
actually emphasises `the team behind` (three words) on slide 3 and `×` (a single glyph) on
slide 9. The invariant that holds across all seven headlines is **one emphasised run**, so
that is what the generator enforces: exactly one `[[…]]` per headline, zero or two being an
error.

## 6. Per-slide headline sizes and one deviant headline

Headlines run 56/58/64/74/78/120px — sized per slide against the space available, not from a
type scale. Each archetype's reference size is the default, overridable with `headlineSize`.

Slide 9 goes further: `font-weight:700; line-height:0.96; letter-spacing:-0.03em` against
the 800/0.9/−0.035em used everywhere else. Because "ROLAND-GARROS × SPORT[GEN]" is two
proper nouns joined by a glyph, it wants slightly looser setting. This is baked into
`09-closing-photo-cta.html` rather than exposed — it is what that archetype *is*.

## 7. Hardcoded colour where tokens would fail

Three places bypass `tokens/colors.css`, and all three are correct to:

- The cover scrim is a four-stop `rgba(8,8,10,…)` gradient at 0.8 → 0.35 → 0.62 → 0.92.
  It is tuned to that photograph's luminance, not to a token.
- The cover's fact-rail hairlines are `rgba(255,255,255,0.28)`, not `var(--line)`. Under
  `data-theme="dark"` `--line` is `rgba(255,255,255,0.12)`, which disappears against a
  photograph. The literal is a deliberate override.
- Slide 6's stacked share bar and legend swatches use a five-step ramp
  `#131316 #3d3d44 #63636a #8a8a90 #b2b2b7`. It exists nowhere in the token files.

The ramp is the one thing here with a real limitation: **it is a light-theme ramp and will
not survive a dark-theme port** — `#131316` on a `#0b0b0d` background is invisible. The
generator assigns the five greys by index and caps `shareBar` at five entries, so a sixth
category cannot silently invent a sixth tone; if slide 6 is ever needed on dark, the ramp
has to be added to the token set first.

## 8. The parent-brand lockup

Slide 3 ends with a 96px `SPORT[GEN]` mark and, under it, the word `SUMMIT` at
`letter-spacing:0.52em; padding-left:5px`. That tracking and that 5px are optical kerning
against the mark's own letterspacing — derived by eye from one specific logo. Exposed as
literal fields (`parentLogo`, `parentWordmark`); a different parent mark will need the
tracking re-tuned in the template.

## 9. Rich inline emphasis

Body copy and sponsorship benefits carry inline `<strong style="color:var(--fg);
font-weight:600;">` mid-sentence — 60-odd instances. A plain-string schema could not express
it and raw HTML in content is rejected, so copy fields take `**bold**` and headlines
additionally take `[[silver]]`, both expanding to the exact markup the reference uses. `\n`
becomes `<br>`, which is also how the cover kicker's trailing `<br>` and slide 6's two-line
headline are reproduced.

## 10. Two structural quirks worth knowing

- **Slide 2's paragraphs inherit their type from their column; slide 3's carry their own.**
  They look like the same component and are not, hence two partials (`para.html`,
  `para-standalone.html`). Merging them would have changed the rendered CSS.
- **Slide 3's "5-up" thumbnail grid holds ten figures**, i.e. two rows. README §4 describes
  it as 5-up, which is the column count. `thumbColumns` defaults to 5 and the row count
  follows from how many thumbs are supplied.

Cosmetically, the reference also contains two whitespace-only text nodes
(`reference/deck.html:82–83`) and per-slide authoring comments. The generator emits its own
comments (`<!-- 03 · BROUGHT TO YOU BY · credibility -->`) and drops the stray nodes;
neither renders, and `verify_roundtrip.py` ignores comments and inter-tag whitespace for
exactly that reason.
