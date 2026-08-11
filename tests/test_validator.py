#!/usr/bin/env python3
"""Guardrail tests — every one of these must be a hard error, not a warning.

    python3 tests/test_validator.py

No test framework: each case deep-copies tests/fixtures/minimal.json, breaks one
thing, and asserts the failure message names the offending field.
"""

from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from new_deck import ContentError, build_deck  # noqa: E402

FIXTURES = REPO / "tests" / "fixtures"
ASSETS = FIXTURES / "assets"
BASE = json.loads((FIXTURES / "minimal.json").read_text(encoding="utf-8"))

results: list[tuple[bool, str]] = []


def case(name: str, mutate, expect: str, *, assets_root: Path = ASSETS) -> None:
    content = copy.deepcopy(BASE)
    mutate(content)
    try:
        build_deck(content, assets_root)
    except ContentError as exc:
        got = str(exc)
        ok = expect.lower() in got.lower()
        results.append((ok, f"{name}\n      expected ~{expect!r}\n      got       {got.splitlines()[0]!r}"
                        if not ok else name))
    else:
        results.append((False, f"{name}\n      expected a ContentError, deck generated cleanly"))


def case_ok(name: str, mutate=lambda c: None, *, assets_root: Path = ASSETS) -> None:
    content = copy.deepcopy(BASE)
    mutate(content)
    try:
        deck, book = build_deck(content, assets_root)
    except ContentError as exc:
        results.append((False, f"{name}\n      unexpected ContentError: {exc}"))
    else:
        results.append((bool(deck.strip()) and len(book.used) > 0, name))


# --- the fixture itself must be valid ---------------------------------------
case_ok("baseline fixture generates")

# --- missing data is an error, never a gap to fill --------------------------
case("missing people[].org",
     lambda c: c["slides"][1]["people"][1].pop("org"),
     "slides[1].people[1].org")
case("missing image alt",
     lambda c: c["slides"][0]["photo"].pop("alt"),
     "slides[0].photo.alt")
case("empty string field",
     lambda c: c["slides"][1].__setitem__("eyebrow", "   "),
     "is empty")
case("unknown archetype",
     lambda c: c["slides"][1].__setitem__("archetype", "timeline"),
     "unknown archetype")

# --- the silver accent: exactly one run per headline ------------------------
case("two silver runs",
     lambda c: c["slides"][0].__setitem__("headline", "A [[placeholder]] cover [[headline]]"),
     "exactly one [[silver]] run")
case("no silver run",
     lambda c: c["slides"][0].__setitem__("headline", "A placeholder cover headline"),
     "exactly one [[silver]] run")

# --- art direction: no colour, no radius, no shadow, no emoji, no raw HTML --
case("colour value in copy",
     lambda c: c["slides"][0].__setitem__("lead", "Our brand colour is #ff6600 and we love it."),
     "monochrome")
case("emoji in copy",
     lambda c: c["slides"][0].__setitem__("lead", "The room is full of investors 🚀 this year."),
     "no emoji")
case("banned CSS in copy",
     lambda c: c["slides"][0].__setitem__("lead", "Rounded via border-radius: 8px looks friendlier."),
     "border-radius")
case("raw HTML in copy",
     lambda c: c["slides"][0].__setitem__("lead", "Please <em>emphasise</em> this properly."),
     "raw HTML")
case("markup in a plain label",
     lambda c: c["slides"][1].__setitem__("eyebrow", "Speakers **2030**"),
     "markup is not allowed")

# --- assets ----------------------------------------------------------------
case("missing image file",
     lambda c: c["slides"][0]["photo"].__setitem__("src", "no-such-photo.jpg"),
     "asset not found")
case("path escapes the assets root",
     lambda c: c["slides"][0]["photo"].__setitem__("src", "../../etc/hosts"),
     "must stay inside the assets root")

# The sample-asset fence can only be exercised where the restricted files actually exist.
# A fresh clone deliberately has none (see examples/ASSETS.md), so these three skip there.
SGN_ASSETS = REPO / "examples" / "assets"
SGN_PANEL = SGN_ASSETS / "photos" / "sportgen-panel.jpg"


def use_sgn_cover(c):
    """Point the fixture at SGN material: both lockups and the cover photograph."""
    c["meta"]["logos"]["lockupOnLight"] = "sgn-investment-summit-black.png"
    c["meta"]["logos"]["lockupOnDark"] = "sgn-investment-summit-white.png"
    c["slides"][0]["photo"]["src"] = "photos/sportgen-panel.jpg"
    del c["slides"][1:]


if SGN_PANEL.is_file():
    case("SGN sample asset without acknowledgement",
         use_sgn_cover, "rights-restricted", assets_root=SGN_ASSETS)

    case_ok("SGN sample assets with meta.sampleAssets set",
            lambda c: (use_sgn_cover(c), c["meta"].__setitem__("sampleAssets", "sgn-internal")),
            assets_root=SGN_ASSETS)

    # A renamed copy, in a directory of otherwise innocent placeholders: only the
    # content hash can catch this one.
    disguised = Path(tempfile.mkdtemp(prefix="sis-disguised-"))
    for placeholder in ASSETS.iterdir():
        shutil.copy2(placeholder, disguised / placeholder.name)
    shutil.copy2(SGN_PANEL, disguised / "our-own-venue-photo.jpg")
    case("SGN sample asset renamed, caught by content hash",
         lambda c: c["slides"][0]["photo"].__setitem__("src", "our-own-venue-photo.jpg"),
         "rights-restricted", assets_root=disguised)
else:
    for skipped in ("SGN sample asset without acknowledgement",
                    "SGN sample assets with meta.sampleAssets set",
                    "SGN sample asset renamed, caught by content hash"):
        results.append((True, f"{skipped} [skipped: examples/assets not populated "
                              "— see examples/ASSETS.md]"))
case("logo without optical caps",
     lambda c: c["slides"][2]["logos"][0].pop("maxHeight"),
     "maxHeight and maxWidth")
case("crop on a slot that has none",
     lambda c: c["slides"][2]["quotes"][0]["thumb"].__setitem__("scale", 1.4),
     "no crop controls")
case("scale without transformOrigin",
     lambda c: c["slides"][1]["people"][0]["photo"].__setitem__("scale", 1.4),
     "transformOrigin")

# --- structural ------------------------------------------------------------
case("duplicate slide label",
     lambda c: c["slides"][2].__setitem__("label", "Speakers"),
     "duplicate slide label")
case("more portraits than the wall holds",
     lambda c: c["slides"][1]["people"].append(
         {"name": "Third Person", "role": "Job Title", "org": "Organisation",
          "photo": {"src": "person.png", "alt": "Third Person"}}),
     "do not fit")

# --- data slides -----------------------------------------------------------
DATA_SLIDE = {
    "archetype": "data-three-zone",
    "label": "Attending",
    "kicker": "Nowhere · 1 January 2030",
    "headline": "Who’s [[attending]]",
    "statRows": [{"figure": "10+", "label": "Placeholder"}],
    "barsLabel": "Seniority (%)",
    "bars": [{"label": "Partner", "value": 60}, {"label": "Director", "value": 40}],
    "shareLabel": "International presence (%)",
    "shareBar": [{"label": "Home", "value": 60}, {"label": "Abroad", "value": 40}],
}


def with_data(**overrides):
    def mutate(c):
        slide = copy.deepcopy(DATA_SLIDE)
        slide.update(overrides)
        c["slides"].append(slide)
    return mutate


case_ok("data slide generates", with_data())
case("share bar not summing to 100",
     with_data(shareBar=[{"label": "Home", "value": 60}, {"label": "Abroad", "value": 30}]),
     "must sum to 100")
case("share bar beyond the five system greys",
     with_data(shareBar=[{"label": str(i), "value": 100 / 6} for i in range(6)]),
     "takes at most 5")
case("bar value out of range",
     with_data(bars=[{"label": "Partner", "value": 140}]),
     "between 0 and 100")

# --- pricing ---------------------------------------------------------------
TIER = {
    "name": "Gold", "price": "10,000€ + VAT", "category": "Standard",
    "includes": "Includes placeholder access", "benefits": ["**Placeholder** benefit."],
}
PRICING = {
    "archetype": "pricing-tiers", "label": "Packages", "eyebrow": "Sponsorship",
    "qualifier": "[ Summary ]", "headline": "Choose your [[package]]",
    "tiers": [TIER, TIER | {"name": "Platinum", "price": "20,000€ + VAT"},
              TIER | {"name": "Diamond", "price": "30,000€ + VAT", "featured": True}],
}


def with_pricing(tiers=None):
    def mutate(c):
        slide = copy.deepcopy(PRICING)
        if tiers is not None:
            slide["tiers"] = copy.deepcopy(tiers)
        c["slides"].append(slide)
    return mutate


case_ok("pricing slide generates", with_pricing())
case("tiers out of price order",
     with_pricing([TIER | {"name": "Diamond", "price": "30,000€ + VAT"},
                   TIER | {"name": "Gold", "price": "10,000€ + VAT", "featured": True}]),
     "out of order")
case("featured tier is not the highest",
     with_pricing([TIER | {"name": "Gold", "price": "10,000€ + VAT", "featured": True},
                   TIER | {"name": "Diamond", "price": "30,000€ + VAT"}]),
     "must be the last")


def main() -> int:
    failed = [msg for ok, msg in results if not ok]
    for ok, msg in results:
        print(("  ok   " if ok else "  FAIL ") + msg)
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
