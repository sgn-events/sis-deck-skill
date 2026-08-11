#!/usr/bin/env python3
"""SIS deck generator — content.json -> a single, hand-editable deck.html.

    python3 scripts/new_deck.py content.json --out ./out
    python3 scripts/new_deck.py content.json --check          # validate only

Stdlib only, no build step. The output directory is a self-contained deck:

    out/
      deck.html        one <section> per slide, every style inline
      deck-stage.js    slide shell (nav, scaling, thumbnail rail, print)
      styles.css       + tokens/
      assets/          only the files the content actually references

Design rules are enforced here rather than trusted to the caller: see validate()
and docs/TEMPLATING-REPORT.md. Missing data is an error, never a gap to fill.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sample_assets import is_sample_asset  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
TEMPLATES = REPO / "templates"
RUNTIME = REPO / "runtime"

# The silver text gradient, byte-for-byte as authored in the reference deck.
SILVER_OPEN = (
    '<span style="background-image:var(--silver);-webkit-background-clip:text;'
    'background-clip:text;-webkit-text-fill-color:transparent;">'
)
STRONG_OPEN = '<strong style="color:var(--fg);font-weight:600;">'

# Slide 6's stacked share bar. Five fixed greys, in this order, and no others:
# a sixth segment would have to invent a tone that is not in the system.
SHARE_GREYS = ("#131316", "#3d3d44", "#63636a", "#8a8a90", "#b2b2b7")

ARCHETYPES = {
    "photo-cover": "01-photo-cover.html",
    "split-argument-photo": "02-split-argument-photo.html",
    "credibility": "03-credibility.html",
    "portrait-wall": "04-portrait-wall.html",
    "category-matrix": "05-category-matrix.html",
    "data-three-zone": "06-data-three-zone.html",
    "logo-wall-quotes": "07-logo-wall-quotes.html",
    "pricing-tiers": "08-pricing-tiers.html",
    "closing-photo-cta": "09-closing-photo-cta.html",
}

# Default headline sizes, per the reference deck. Each is overridable per slide
# with `headlineSize` because the reference itself tunes 56/58/64/74/78/120.
DEFAULT_HEADLINE_SIZE = {
    "photo-cover": 120,
    "split-argument-photo": 74,
    "credibility": 64,
    "data-three-zone": 56,
    "logo-wall-quotes": 78,
    "pricing-tiers": 58,
    "closing-photo-cta": 78,
}

EMOJI_RE = re.compile(
    "[" "\U0001f300-\U0001faff" "\U00002600-\U000027bf" "\U0001f000-\U0001f2ff"
    "\U0000fe0f" "\U0001f900-\U0001f9ff" "]"
)
COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(")
RAW_HTML_RE = re.compile(r"<\s*/?\s*[a-zA-Z]")
BANNED_CSS = ("border-radius", "box-shadow", "border-width", "text-shadow", "!important")


class ContentError(Exception):
    """A fatal problem in content.json, reported with the path to the field."""


def fail(where: str, message: str) -> None:
    raise ContentError(f"{where}: {message}")


# ---------------------------------------------------------------------------
# Tiny template renderer
# ---------------------------------------------------------------------------

_IF_RE = re.compile(r"\{\{#if (\w+)\}\}(.*?)\{\{/if\}\}", re.DOTALL)
_RAW_RE = re.compile(r"\{\{\{(\w+)\}\}\}")
_VAR_RE = re.compile(r"\{\{(\w+)\}\}")

_cache: dict[str, str] = {}


def load_template(name: str) -> str:
    if name not in _cache:
        path = TEMPLATES / name
        if not path.exists():
            raise ContentError(f"missing template {path}")
        _cache[name] = path.read_text(encoding="utf-8")
    return _cache[name]


def render(template_name: str, ctx: dict) -> str:
    """Fill a template.

    {{key}}    HTML-escaped scalar
    {{{key}}}  pre-rendered fragment (generator-produced only, never raw input)
    {{#if k}}…{{/if}}  dropped when k is absent or falsy
    """
    out = load_template(template_name)
    out = _IF_RE.sub(lambda m: m.group(2) if ctx.get(m.group(1)) else "", out)

    def raw(m: re.Match) -> str:
        key = m.group(1)
        if key not in ctx:
            raise ContentError(f"template {template_name} wants {{{{{{{key}}}}}}}")
        return str(ctx[key])

    def var(m: re.Match) -> str:
        key = m.group(1)
        if key not in ctx:
            raise ContentError(f"template {template_name} wants {{{{{key}}}}}")
        value = ctx[key]
        return html.escape(str(value), quote=True)

    out = _RAW_RE.sub(raw, out)
    out = _VAR_RE.sub(var, out)
    return out.rstrip("\n")


def each(template_name: str, contexts: list[dict], sep: str = "\n") -> str:
    return sep.join(render(template_name, c) for c in contexts)


# ---------------------------------------------------------------------------
# Copy conventions
# ---------------------------------------------------------------------------


def inline(text: str, where: str) -> str:
    """Body copy: escape, then **bold** -> the deck's <strong>, \\n -> <br>."""
    check_string(text, where)
    out = html.escape(text, quote=False)
    out = re.sub(r"\*\*(.+?)\*\*", lambda m: STRONG_OPEN + m.group(1) + "</strong>", out)
    return out.replace("\n", "<br>")


def headline(text: str, where: str) -> str:
    """Headline: exactly one [[silver run]], plus the inline conventions."""
    check_string(text, where)
    runs = re.findall(r"\[\[(.+?)\]\]", text)
    if len(runs) != 1:
        fail(
            where,
            f"a headline needs exactly one [[silver]] run, found {len(runs)}. "
            "The silver text gradient is the deck's only accent and marks one "
            "run per headline — e.g. \"Europe's leading sport [[investment]] event\".",
        )
    out = html.escape(text, quote=False)
    out = re.sub(r"\[\[(.+?)\]\]", lambda m: SILVER_OPEN + m.group(1) + "</span>", out)
    out = re.sub(r"\*\*(.+?)\*\*", lambda m: STRONG_OPEN + m.group(1) + "</strong>", out)
    return out.replace("\n", "<br>")


def plain(text: str, where: str) -> str:
    """Mono labels, names, captions: validated, no markup at all.

    Returns the text unescaped — it lands in a `{{key}}` slot, and the renderer
    escapes those. inline() and headline() are the ones that escape, because
    their output is HTML and goes into a `{{{key}}}` slot.
    """
    check_string(text, where)
    if "**" in text or "[[" in text:
        fail(where, "markup is not allowed in this field — it is a plain label")
    return text


def check_string(text: str, where: str) -> None:
    if not isinstance(text, str):
        fail(where, f"expected a string, got {type(text).__name__}")
    if not text.strip():
        fail(where, "is empty — missing content is an error, not a gap to fill")
    if EMOJI_RE.search(text):
        fail(where, "contains an emoji. The SIS art direction has no emoji and no icons.")
    if COLOR_RE.search(text):
        fail(
            where,
            "contains a colour value. The deck is monochrome: the only accent is the "
            "silver text gradient, and every tone comes from tokens/colors.css.",
        )
    for banned in BANNED_CSS:
        if banned in text:
            fail(where, f"contains '{banned}'. Corners are sharp, rules are 1px, nothing casts a shadow.")
    if RAW_HTML_RE.search(text):
        fail(
            where,
            "contains raw HTML. Content is escaped by design — use **bold**, "
            "[[silver]] and \\n for a line break.",
        )


# ---------------------------------------------------------------------------
# Content access helpers
# ---------------------------------------------------------------------------


def need(obj: dict, key: str, where: str):
    if not isinstance(obj, dict):
        fail(where, f"expected an object, got {type(obj).__name__}")
    if key not in obj or obj[key] in (None, "", [], {}):
        fail(f"{where}.{key}", "is required and missing")
    return obj[key]


def need_list(obj: dict, key: str, where: str, *, count: int | None = None,
              minimum: int | None = None, maximum: int | None = None) -> list:
    value = need(obj, key, where)
    at = f"{where}.{key}"
    if not isinstance(value, list):
        fail(at, f"expected a list, got {type(value).__name__}")
    if count is not None and len(value) != count:
        fail(at, f"needs exactly {count} entries, got {len(value)}")
    if minimum is not None and len(value) < minimum:
        fail(at, f"needs at least {minimum} entries, got {len(value)}")
    if maximum is not None and len(value) > maximum:
        fail(at, f"takes at most {maximum} entries, got {len(value)}")
    return value


def need_int(obj: dict, key: str, where: str, lo: int, hi: int) -> float:
    value = need(obj, key, where)
    at = f"{where}.{key}"
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(at, f"expected a number, got {type(value).__name__}")
    if not lo <= value <= hi:
        fail(at, f"must be between {lo} and {hi}, got {value}")
    return value


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------


class AssetBook:
    """Collects every referenced asset, validates it, and copies it once."""

    def __init__(self, assets_root: Path, allow_samples: bool):
        self.root = assets_root
        self.allow_samples = allow_samples
        self.used: dict[str, Path] = {}

    def resolve(self, rel: str, where: str) -> str:
        if not isinstance(rel, str) or not rel.strip():
            fail(where, "asset path is empty")
        norm = rel.replace("\\", "/").lstrip("/")
        if norm.startswith("./"):
            norm = norm[2:]
        if ".." in norm.split("/"):
            fail(where, f"asset path must stay inside the assets root: {rel!r}")
        source = self.root / norm
        if not source.is_file():
            fail(
                where,
                f"asset not found: {source}\n"
                "  Every image must exist before the deck is generated. Supply your own "
                "photography and logos, or see examples/ASSETS.md for the sample set.",
            )
        if not self.allow_samples and is_sample_asset(norm, source.read_bytes()):
            fail(
                where,
                f"{norm} is an SGN sample asset and is rights-restricted.\n"
                "  Speaker portraits, media logos and event lockups from the SGN handoff are "
                "cleared for SGN event marketing only. Supply your own assets for this deck.\n"
                "  (Matched by name or by file contents — renaming it does not clear the rights.)",
            )
        self.used[norm] = source
        return "./assets/" + norm

    def copy_into(self, out_dir: Path) -> int:
        for norm, source in sorted(self.used.items()):
            target = out_dir / "assets" / norm
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return len(self.used)


def image(spec, where: str, book: AssetBook, *, default_position: str | None = None,
          crops_allowed: bool = True) -> dict:
    """Normalise a `string | {src, alt, ...}` image field.

    The optional crop keys exist because the reference deck hand-tunes 8 of its
    25 portraits — head position in a photograph is not derivable from content.
    """
    if isinstance(spec, str):
        spec = {"src": spec}
    if not isinstance(spec, dict):
        fail(where, f"expected an image path or object, got {type(spec).__name__}")

    src = book.resolve(need(spec, "src", where), f"{where}.src")
    alt = plain(need(spec, "alt", where), f"{where}.alt")

    if not crops_allowed:
        for key in ("objectPosition", "scale", "transformOrigin"):
            if key in spec:
                fail(f"{where}.{key}", "this slot fills its frame; it has no crop controls")

    position = spec.get("objectPosition", default_position)
    if position is not None:
        check_style_value(position, f"{where}.objectPosition")

    crop = ""
    if position is not None and default_position is None:
        crop += f"object-position:{position};"
    scale = spec.get("scale")
    if scale is not None:
        if isinstance(scale, bool) or not isinstance(scale, (int, float)):
            fail(f"{where}.scale", "expected a number, e.g. 1.5")
        origin = spec.get("transformOrigin")
        if origin is None:
            fail(f"{where}.transformOrigin", "is required whenever scale is set")
        check_style_value(origin, f"{where}.transformOrigin")
        crop += f"transform:scale({scale});transform-origin:{origin};"
    elif "transformOrigin" in spec:
        fail(f"{where}.transformOrigin", "only applies together with scale")

    return {
        "src": src,
        "alt": alt,
        "position": position,
        "crop": crop,
        "keep_color": bool(spec.get("keepColor")),
        "max_height": spec.get("maxHeight"),
        "max_width": spec.get("maxWidth"),
    }


def check_style_value(value, where: str) -> None:
    if not isinstance(value, str) or not value.strip():
        fail(where, "expected a CSS value such as 'center 15%'")
    if not re.fullmatch(r"[a-z0-9%.\s-]+", value):
        fail(where, f"unexpected CSS value {value!r} — use keywords and percentages only")


# ---------------------------------------------------------------------------
# Archetype builders
# ---------------------------------------------------------------------------


def build_photo_cover(slide: dict, where: str, ctx: dict) -> str:
    book, meta = ctx["book"], ctx["meta"]
    photo = image(need(slide, "photo", where), f"{where}.photo", book,
                  default_position="center 42%")
    facts = need_list(slide, "factRail", where, count=3)
    return render(
        ARCHETYPES["photo-cover"],
        {
            "label": slide["label"],
            "photo_src": photo["src"],
            "photo_alt": photo["alt"],
            "photo_position": photo["position"],
            "lockup_src": meta["lockup_on_dark"],
            "event": meta["event"],
            "kicker": inline(need(slide, "kicker", where), f"{where}.kicker"),
            "headline": headline(need(slide, "headline", where), f"{where}.headline"),
            "headline_size": slide.get("headlineSize", DEFAULT_HEADLINE_SIZE["photo-cover"]),
            "lead": inline(need(slide, "lead", where), f"{where}.lead"),
            "fact_left": plain(facts[0], f"{where}.factRail[0]"),
            "fact_center": plain(facts[1], f"{where}.factRail[1]"),
            "fact_right": plain(facts[2], f"{where}.factRail[2]"),
        },
    )


def build_split_argument_photo(slide: dict, where: str, ctx: dict) -> str:
    book = ctx["book"]
    paras = need_list(slide, "paras", where, minimum=1)
    stats = need_list(slide, "stats", where, minimum=1, maximum=4)
    photo = image(need(slide, "photo", where), f"{where}.photo", book, crops_allowed=False)
    meta_left = need(slide, "metaLeft", where)
    meta_right = need(slide, "metaRight", where)

    stat_ctxs = []
    for i, stat in enumerate(stats):
        at = f"{where}.stats[{i}]"
        stat_ctxs.append({
            "pad": "18px 0" if i == 0 else "18px 0 18px 20px",
            "border": "" if i == 0 else "border-left:1px solid var(--line);",
            "figure": plain(need(stat, "figure", at), f"{at}.figure"),
            "label": plain(need(stat, "label", at), f"{at}.label"),
            "note": plain(need(stat, "note", at), f"{at}.note"),
        })

    return render(
        ARCHETYPES["split-argument-photo"],
        {
            "label": slide["label"],
            "banner": ctx["banner"],
            "eyebrow": plain(need(slide, "eyebrow", where), f"{where}.eyebrow"),
            "headline": headline(need(slide, "headline", where), f"{where}.headline"),
            "headline_size": slide.get("headlineSize", DEFAULT_HEADLINE_SIZE["split-argument-photo"]),
            "paras": each("partials/para.html", [
                {"text": inline(p, f"{where}.paras[{i}]")} for i, p in enumerate(paras)
            ]),
            "stat_count": len(stats),
            "stats": each("partials/stat-cell.html", stat_ctxs),
            "meta_left_label": plain(need(meta_left, "label", f"{where}.metaLeft"), f"{where}.metaLeft.label"),
            "meta_left_text": inline(need(meta_left, "text", f"{where}.metaLeft"), f"{where}.metaLeft.text"),
            "meta_right_label": plain(need(meta_right, "label", f"{where}.metaRight"), f"{where}.metaRight.label"),
            "meta_right_text": inline(need(meta_right, "text", f"{where}.metaRight"), f"{where}.metaRight.text"),
            "photo_src": photo["src"],
            "photo_alt": photo["alt"],
            "photo_caption": plain(need(slide, "photoCaption", where), f"{where}.photoCaption"),
        },
    )


def build_credibility(slide: dict, where: str, ctx: dict) -> str:
    book = ctx["book"]
    thumbs = need_list(slide, "thumbs", where, minimum=1)
    paras = need_list(slide, "paras", where, count=2)
    rows = need_list(slide, "figureRows", where, minimum=1)
    parent = need(slide, "parentLogo", where)
    parent_img = image(parent, f"{where}.parentLogo", book, crops_allowed=False)

    thumb_ctxs = []
    for i, person in enumerate(thumbs):
        at = f"{where}.thumbs[{i}]"
        photo = image(need(person, "photo", at), f"{at}.photo", book)
        thumb_ctxs.append({
            "photo_src": photo["src"],
            "photo_alt": photo["alt"],
            "crop": photo["crop"],
            "name": plain(need(person, "name", at), f"{at}.name"),
            "org": plain(need(person, "org", at), f"{at}.org"),
        })

    row_ctxs = []
    for i, row in enumerate(rows):
        at = f"{where}.figureRows[{i}]"
        row_ctxs.append({
            "extra_border": "border-bottom:1px solid var(--line);" if i == len(rows) - 1 else "",
            "figure": plain(need(row, "figure", at), f"{at}.figure"),
            "text": inline(need(row, "text", at), f"{at}.text"),
        })

    return render(
        ARCHETYPES["credibility"],
        {
            "label": slide["label"],
            "banner": ctx["banner"],
            "eyebrow": plain(need(slide, "eyebrow", where), f"{where}.eyebrow"),
            "headline": headline(need(slide, "headline", where), f"{where}.headline"),
            "headline_size": slide.get("headlineSize", DEFAULT_HEADLINE_SIZE["credibility"]),
            "thumbs_label": plain(need(slide, "thumbsLabel", where), f"{where}.thumbsLabel"),
            "thumb_columns": slide.get("thumbColumns", 5),
            "thumbs": each("partials/speaker-thumb.html", thumb_ctxs),
            "parent_logo_src": parent_img["src"],
            "parent_logo_alt": parent_img["alt"],
            "parent_wordmark": plain(need(slide, "parentWordmark", where), f"{where}.parentWordmark"),
            # This slide's paragraphs sit in a 2-up grid and carry their own type
            # scale, unlike slide 2's, which inherit from their column.
            "paras": each("partials/para-standalone.html", [
                {"text": inline(p, f"{where}.paras[{i}]")} for i, p in enumerate(paras)
            ]),
            "figure_rows": each("partials/figure-row.html", row_ctxs),
        },
    )


def build_portrait_wall(slide: dict, where: str, ctx: dict) -> str:
    book = ctx["book"]
    people = need_list(slide, "people", where, minimum=1)
    columns = slide.get("columns", 5)
    rows = slide.get("rows")
    if rows is None:
        rows = -(-len(people) // columns)
    if len(people) > columns * rows:
        fail(
            f"{where}.people",
            f"{len(people)} portraits do not fit a {columns}×{rows} wall — "
            "raise columns/rows or split the slide.",
        )

    cards = []
    for i, person in enumerate(people):
        at = f"{where}.people[{i}]"
        photo = image(need(person, "photo", at), f"{at}.photo", book, default_position="center 15%")
        cards.append({
            "photo_src": photo["src"],
            "photo_alt": photo["alt"],
            "photo_position": photo["position"],
            "crop": photo["crop"],
            "index": f"{i + 1:02d}",
            "name": plain(need(person, "name", at), f"{at}.name"),
            "role": plain(need(person, "role", at), f"{at}.role"),
            "org": plain(need(person, "org", at), f"{at}.org"),
        })

    return render(
        ARCHETYPES["portrait-wall"],
        {
            "label": slide["label"],
            "banner": ctx["banner"],
            "eyebrow": plain(need(slide, "eyebrow", where), f"{where}.eyebrow"),
            "qualifier": plain(need(slide, "qualifier", where), f"{where}.qualifier"),
            "columns": columns,
            "rows": rows,
            "people": each("partials/portrait-card.html", cards),
        },
    )


def build_category_matrix(slide: dict, where: str, ctx: dict) -> str:
    categories = need_list(slide, "categories", where, minimum=1)
    columns = slide.get("columns", 3)

    cells = []
    for i, cat in enumerate(categories):
        at = f"{where}.categories[{i}]"
        items = need_list(cat, "items", at, minimum=1)
        item_ctxs = []
        for j, item in enumerate(items):
            iat = f"{at}.items[{j}]"
            if isinstance(item, str):
                item = {"name": item}
            qualifier = item.get("qualifier")
            item_ctxs.append({
                "name": plain(need(item, "name", iat), f"{iat}.name"),
                "qualifier": render(
                    "partials/matrix-item-qualifier.html",
                    {"text": plain(qualifier, f"{iat}.qualifier")},
                ) if qualifier else "",
            })
        collapse = ""
        if i % columns:
            collapse += "margin-left:-1px;"
        if i >= columns:
            collapse += "margin-top:-1px;"
        cells.append({
            "collapse": collapse,
            "index": f"{i + 1:02d}",
            "name": plain(need(cat, "name", at), f"{at}.name"),
            "items": each("partials/matrix-item.html", item_ctxs, sep=""),
        })

    return render(
        ARCHETYPES["category-matrix"],
        {
            "label": slide["label"],
            "banner": ctx["banner"],
            "eyebrow": plain(need(slide, "eyebrow", where), f"{where}.eyebrow"),
            "qualifier": plain(need(slide, "qualifier", where), f"{where}.qualifier"),
            "columns": columns,
            "cells": each("partials/matrix-cell.html", cells),
        },
    )


def build_data_three_zone(slide: dict, where: str, ctx: dict) -> str:
    stat_rows = need_list(slide, "statRows", where, minimum=1)
    bars = need_list(slide, "bars", where, minimum=1)
    share = need_list(slide, "shareBar", where, minimum=2, maximum=len(SHARE_GREYS))

    stat_ctxs = []
    for i, row in enumerate(stat_rows):
        at = f"{where}.statRows[{i}]"
        stat_ctxs.append({
            "extra_border": "border-bottom:1px solid var(--line);" if i == len(stat_rows) - 1 else "",
            "figure": plain(need(row, "figure", at), f"{at}.figure"),
            "label": plain(need(row, "label", at), f"{at}.label"),
        })

    bar_ctxs = []
    for i, bar in enumerate(bars):
        at = f"{where}.bars[{i}]"
        bar_ctxs.append({
            "label": plain(need(bar, "label", at), f"{at}.label"),
            "value": fmt_number(need_int(bar, "value", at, 0, 100)),
        })

    total = 0.0
    seg_ctxs, legend_ctxs = [], []
    for i, seg in enumerate(share):
        at = f"{where}.shareBar[{i}]"
        value = need_int(seg, "value", at, 0, 100)
        total += value
        seg_ctxs.append({"value": fmt_number(value), "swatch": SHARE_GREYS[i]})
        legend_ctxs.append({
            "extra_border": "border-bottom:1px solid var(--line);" if i == len(share) - 1 else "",
            "swatch": SHARE_GREYS[i],
            "label": plain(need(seg, "label", at), f"{at}.label"),
            "value": fmt_number(value),
        })
    if round(total, 6) != 100:
        fail(f"{where}.shareBar", f"values must sum to 100, they sum to {fmt_number(total)}")

    return render(
        ARCHETYPES["data-three-zone"],
        {
            "label": slide["label"],
            "banner": ctx["banner"],
            "kicker": plain(need(slide, "kicker", where), f"{where}.kicker"),
            "headline": headline(need(slide, "headline", where), f"{where}.headline"),
            "headline_size": slide.get("headlineSize", DEFAULT_HEADLINE_SIZE["data-three-zone"]),
            "stat_rows": each("partials/stat-row.html", stat_ctxs),
            "bars_label": plain(need(slide, "barsLabel", where), f"{where}.barsLabel"),
            "bars": each("partials/bar-row.html", bar_ctxs),
            "share_label": plain(need(slide, "shareLabel", where), f"{where}.shareLabel"),
            "share_segments": each("partials/share-segment.html", seg_ctxs),
            "legend_rows": each("partials/legend-row.html", legend_ctxs),
        },
    )


def build_logo_wall_quotes(slide: dict, where: str, ctx: dict) -> str:
    book = ctx["book"]
    logos = need_list(slide, "logos", where, minimum=1)
    quotes = need_list(slide, "quotes", where, minimum=1)

    logo_ctxs = []
    for i, spec in enumerate(logos):
        at = f"{where}.logos[{i}]"
        logo = image(spec, at, book, crops_allowed=False)
        if logo["max_height"] is None or logo["max_width"] is None:
            fail(
                at,
                "needs maxHeight and maxWidth. Logo lockups have wildly different aspect "
                "ratios; the wall only reads evenly when each cap is set by eye.",
            )
        logo_ctxs.append({
            "src": logo["src"],
            "alt": logo["alt"],
            "max_height": fmt_number(logo["max_height"]),
            "max_width": fmt_number(logo["max_width"]),
            # One-colour by default. keepColor is the documented exemption for
            # lockups whose licence forbids recolouring (e.g. Canal+).
            "monochrome": "" if logo["keep_color"] else "filter:brightness(0);",
        })

    quote_ctxs = []
    for i, quote in enumerate(quotes):
        at = f"{where}.quotes[{i}]"
        thumb = image(need(quote, "thumb", at), f"{at}.thumb", book, crops_allowed=False)
        quote_ctxs.append({
            "thumb_src": thumb["src"],
            "thumb_alt": thumb["alt"],
            "quote": plain(need(quote, "quote", at), f"{at}.quote"),
        })

    return render(
        ARCHETYPES["logo-wall-quotes"],
        {
            "label": slide["label"],
            "banner": ctx["banner"],
            "eyebrow": plain(need(slide, "eyebrow", where), f"{where}.eyebrow"),
            "headline": headline(need(slide, "headline", where), f"{where}.headline"),
            "headline_size": slide.get("headlineSize", DEFAULT_HEADLINE_SIZE["logo-wall-quotes"]),
            "lead": inline(need(slide, "lead", where), f"{where}.lead"),
            "logos": each("partials/logo.html", logo_ctxs),
            "quotes_label": plain(need(slide, "quotesLabel", where), f"{where}.quotesLabel"),
            "quotes": each("partials/quote-card.html", quote_ctxs),
        },
    )


def build_pricing_tiers(slide: dict, where: str, ctx: dict) -> str:
    tiers = need_list(slide, "tiers", where, minimum=2, maximum=4)

    prices = []
    tier_ctxs = []
    for i, tier in enumerate(tiers):
        at = f"{where}.tiers[{i}]"
        benefits = need_list(tier, "benefits", at, minimum=1)
        rows = []
        for j, benefit in enumerate(benefits):
            bat = f"{at}.benefits[{j}]"
            if isinstance(benefit, str):
                benefit = {"text": benefit}
            text = inline(need(benefit, "text", bat), f"{bat}.text")
            subs = benefit.get("subs") or []
            if subs:
                rows.append(("partials/benefit-row-subs.html", {
                    "text": text,
                    "subs": each("partials/benefit-sub.html", [
                        {"text": inline(s, f"{bat}.subs[{k}]")} for k, s in enumerate(subs)
                    ], sep=""),
                }))
            else:
                rows.append(("partials/benefit-row.html", {"text": text}))

        price = plain(need(tier, "price", at), f"{at}.price")
        prices.append(parse_price(price))
        tier_ctxs.append({
            # Only the top tier is filled; everything else stays on --bg.
            "featured_fill": "background:var(--panel-2);" if tier.get("featured") else "",
            "name": plain(need(tier, "name", at), f"{at}.name"),
            "price": price,
            "category_label": plain(tier.get("categoryLabel", "Category"), f"{at}.categoryLabel"),
            "category": plain(need(tier, "category", at), f"{at}.category"),
            "includes": plain(need(tier, "includes", at), f"{at}.includes"),
            "benefits": "\n".join(render(name, c) for name, c in rows),
        })

    featured = [i for i, t in enumerate(tiers) if t.get("featured")]
    if len(featured) > 1:
        fail(f"{where}.tiers", "only one tier may be featured")
    if featured and featured[0] != len(tiers) - 1:
        fail(f"{where}.tiers", "the featured tier must be the last (highest) one")
    if all(p is not None for p in prices) and prices != sorted(prices):
        fail(f"{where}.tiers", f"tiers read low to high; these prices are out of order: {prices}")

    return render(
        ARCHETYPES["pricing-tiers"],
        {
            "label": slide["label"],
            "banner": ctx["banner"],
            "eyebrow": plain(need(slide, "eyebrow", where), f"{where}.eyebrow"),
            "qualifier": plain(need(slide, "qualifier", where), f"{where}.qualifier"),
            "headline": headline(need(slide, "headline", where), f"{where}.headline"),
            "headline_size": slide.get("headlineSize", DEFAULT_HEADLINE_SIZE["pricing-tiers"]),
            "tier_count": len(tiers),
            "tiers": each("partials/tier-card.html", tier_ctxs),
        },
    )


def build_closing_photo_cta(slide: dict, where: str, ctx: dict) -> str:
    book = ctx["book"]
    photo = image(need(slide, "photo", where), f"{where}.photo", book, default_position="center 66%")
    captions = need_list(slide, "photoCaptions", where, count=2)
    return render(
        ARCHETYPES["closing-photo-cta"],
        {
            "label": slide["label"],
            "banner": ctx["banner"],
            "eyebrow": plain(need(slide, "eyebrow", where), f"{where}.eyebrow"),
            "qualifier": plain(need(slide, "qualifier", where), f"{where}.qualifier"),
            "headline": headline(need(slide, "headline", where), f"{where}.headline"),
            "headline_size": slide.get("headlineSize", DEFAULT_HEADLINE_SIZE["closing-photo-cta"]),
            "lead": inline(need(slide, "lead", where), f"{where}.lead"),
            "photo_src": photo["src"],
            "photo_alt": photo["alt"],
            "photo_position": photo["position"],
            "caption_left": plain(captions[0], f"{where}.photoCaptions[0]"),
            "caption_right": plain(captions[1], f"{where}.photoCaptions[1]"),
        },
    )


BUILDERS = {
    "photo-cover": build_photo_cover,
    "split-argument-photo": build_split_argument_photo,
    "credibility": build_credibility,
    "portrait-wall": build_portrait_wall,
    "category-matrix": build_category_matrix,
    "data-three-zone": build_data_three_zone,
    "logo-wall-quotes": build_logo_wall_quotes,
    "pricing-tiers": build_pricing_tiers,
    "closing-photo-cta": build_closing_photo_cta,
}


def fmt_number(value) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def parse_price(text: str):
    digits = re.sub(r"[^\d]", "", text.split("+")[0])
    return int(digits) if digits else None


# ---------------------------------------------------------------------------
# Deck assembly
# ---------------------------------------------------------------------------


def build_deck(content: dict, assets_root: Path) -> tuple[str, AssetBook]:
    if not isinstance(content, dict):
        raise ContentError("content.json must be an object with meta and slides")

    meta_in = need(content, "meta", "content")
    slides_in = need_list(content, "slides", "content", minimum=1)

    allow_samples = meta_in.get("sampleAssets") == "sgn-internal"
    book = AssetBook(assets_root, allow_samples)

    event = plain(need(meta_in, "event", "meta"), "meta.event")
    logos = need(meta_in, "logos", "meta")
    meta = {
        "event": event,
        "lockup_on_light": book.resolve(need(logos, "lockupOnLight", "meta.logos"), "meta.logos.lockupOnLight"),
        "lockup_on_dark": book.resolve(need(logos, "lockupOnDark", "meta.logos"), "meta.logos.lockupOnDark"),
    }
    banner_meta = meta_in.get("bannerMeta") or " · ".join(
        [plain(need(meta_in, "date", "meta"), "meta.date"), plain(need(meta_in, "city", "meta"), "meta.city")]
    )
    banner = render("partials/banner.html", {
        "lockup_src": meta["lockup_on_light"],
        "event": event,
        "banner_meta": plain(banner_meta, "meta.bannerMeta"),
    })

    rendered = []
    seen_labels = set()
    for i, slide in enumerate(slides_in):
        where = f"slides[{i}]"
        archetype = need(slide, "archetype", where)
        if archetype not in BUILDERS:
            fail(
                f"{where}.archetype",
                f"unknown archetype {archetype!r}. Available: {', '.join(sorted(BUILDERS))}",
            )
        label = plain(need(slide, "label", where), f"{where}.label")
        if label in seen_labels:
            fail(f"{where}.label", f"duplicate slide label {label!r} — the rail needs distinct names")
        seen_labels.add(label)
        slide = dict(slide, label=label)
        ctx = {"book": book, "meta": meta, "banner": banner if archetype != "photo-cover" else ""}
        # A signpost comment per slide, so the single output file stays as
        # navigable by hand as the deck it was derived from.
        marker = f"      <!-- {i + 1:02d} · {label.upper()} · {archetype} -->"
        rendered.append(marker + "\n" + BUILDERS[archetype](slide, where, ctx))

    title = meta_in.get("title") or f"{event} — Deck"
    deck = render("shell.html", {
        "lang": meta_in.get("lang", "en"),
        "title": plain(title, "meta.title"),
        "width": int(meta_in.get("width", 1920)),
        "height": int(meta_in.get("height", 1080)),
        "slides": "\n\n".join(rendered),
    })
    return deck + "\n", book


def copy_runtime(out_dir: Path, fonts: str) -> None:
    shutil.copy2(RUNTIME / "deck-stage.js", out_dir / "deck-stage.js")
    (out_dir / "tokens").mkdir(parents=True, exist_ok=True)
    for token in (RUNTIME / "tokens").glob("*.css"):
        if token.name == "fonts.selfhosted.css" and fonts != "selfhosted":
            continue
        shutil.copy2(token, out_dir / "tokens" / token.name)

    styles = (RUNTIME / "styles.css").read_text(encoding="utf-8")
    if fonts == "selfhosted":
        styles = styles.replace("./tokens/fonts.css", "./tokens/fonts.selfhosted.css")
        font_dir = RUNTIME / "fonts"
        needed = re.findall(r"\.\./fonts/([^']+)", (RUNTIME / "tokens" / "fonts.selfhosted.css").read_text())
        missing = [n for n in needed if not (font_dir / n).is_file()]
        if missing:
            raise ContentError(
                "--fonts selfhosted needs the font binaries in runtime/fonts/. Missing: "
                + ", ".join(sorted(missing))
                + "\n  See runtime/tokens/fonts.selfhosted.css for the expected filenames."
            )
        target = out_dir / "fonts"
        target.mkdir(parents=True, exist_ok=True)
        for name in needed:
            shutil.copy2(font_dir / name, target / name)
    (out_dir / "styles.css").write_text(styles, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate an SIS deck from content.json")
    parser.add_argument("content", type=Path, help="path to content.json")
    parser.add_argument("--out", type=Path, help="output directory (default ./out)")
    parser.add_argument("--assets-root", type=Path,
                        help="root that content asset paths are relative to "
                             "(default: <content dir>/assets)")
    parser.add_argument("--fonts", choices=("google", "selfhosted"), default="google",
                        help="webfont delivery (default google)")
    parser.add_argument("--check", action="store_true", help="validate only, write nothing")
    args = parser.parse_args(argv)

    try:
        raw = args.content.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read {args.content}: {exc}", file=sys.stderr)
        return 2
    try:
        content = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"error: {args.content} is not valid JSON: {exc}", file=sys.stderr)
        return 2

    assets_root = args.assets_root or args.content.resolve().parent / "assets"
    try:
        deck, book = build_deck(content, assets_root)
    except ContentError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.check:
        print(f"ok: {len(content['slides'])} slides, {len(book.used)} assets referenced")
        return 0

    out_dir = (args.out or Path("out")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "deck.html").write_text(deck, encoding="utf-8")
    try:
        copy_runtime(out_dir, args.fonts)
    except ContentError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    copied = book.copy_into(out_dir)
    print(f"wrote {out_dir / 'deck.html'} — {len(content['slides'])} slides, {copied} assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
