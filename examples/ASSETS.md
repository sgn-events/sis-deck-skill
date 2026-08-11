# Sample assets — provenance and why they are not in this repo

`examples/content.json` reproduces the SGN Investment Summit deck exactly, which means it
references 54 image files. **None of them are committed.** `examples/assets/` is in
`.gitignore`.

## Why

The speaker portraits, media outlet logos and event lockups belong to SGN and to the
respective outlets and individuals. They are cleared for **SGN event marketing use only**.
Committing them would put rights-restricted likenesses and third-party trademarks into a
git history forever, and would invite exactly the reuse the licence forbids. They are also
3.9 MB, which is a poor thing to carry in a template repo.

The generator enforces this rather than trusting it: `scripts/sample_assets.py` lists all
55 files by path and by SHA-256, and `new_deck.py` refuses to place any of them in a deck
unless the content sets `meta.sampleAssets: "sgn-internal"`. Renaming a file does not defeat
the check — the content hash catches it. `examples/content.json` is the only content file in
this repo that carries that flag, and nothing else should.

## Where they come from

The `handoff-sis-deck` design bundle, at `handoff-sis-deck/deck/assets/`:

| Path | What | Count |
|---|---|---|
| `sgn-investment-summit-black.png` / `-white.png` | Event lockup, for the light banner and the dark cover | 2 |
| `sportgen-logo-black.png` | Parent brand mark (slide 3) | 1 |
| `photos/` | `sportgen-panel.jpg` (cover), `fireside-marc-lasry.jpg` (slide 2), `roland-garros.jpg` (slide 9), `hotel-crillon.jpg` (spare, unused) | 4 |
| `speakers/` | 15 finance-segment portraits (slide 4) + 10 `sgn-*` SPORT[GEN] portraits (slide 3) | 25 |
| `media/` | 19 outlet logos (slide 7) | 19 |
| `media/press/` | 4 press thumbnails (slide 7) | 4 |

## Copying them in

To reproduce the reference deck locally, point the assets root at the bundle:

```bash
python3 scripts/new_deck.py examples/content.json --out ./out --assets-root ../handoff-sis-deck/deck/assets
```

Or copy them once into the ignored directory:

```bash
mkdir -p examples/assets && cp -R ../handoff-sis-deck/deck/assets/. examples/assets/
```

Adjust the relative path to wherever the bundle lives. If the files are absent, the
generator stops with `asset not found: …` naming the exact field — it never silently skips
an image.

## For your own deck

Supply your own photography, portraits and logos, in the same directory shape
(`photos/`, `speakers/`, `media/`), and point `--assets-root` at it. Requirements the art
direction imposes:

- **Portraits**: any aspect ratio; they are cropped to 1:1 (slide 3) or to the wall cell
  (slide 4) and forced to grayscale. Faces sitting high or low in frame need
  `objectPosition`, and tight crops need `scale` + `transformOrigin` — 8 of the reference
  deck's 25 portraits do.
- **Logos**: transparent PNG or SVG, on no background. They are flattened to solid black,
  so a logo that only reads in its own colour will not survive; ask for a one-colour
  version, or use `keepColor: true` and note why.
- **Photographs**: at least 1920px on the long edge. The cover keeps its colour under a
  dark scrim, so it wants a dark or dimly-lit frame with room for a headline at the bottom
  left. Every other photograph is grayscaled.
