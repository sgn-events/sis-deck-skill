#!/usr/bin/env python3
"""Prove that a generated deck matches the reference deck.

    python3 scripts/verify_roundtrip.py out/deck.html reference/deck.html

Compares the two files as normalised token streams rather than byte-for-byte:
whitespace between tags and source indentation carry no meaning in HTML, and the
reference was authored by hand. Everything that *does* render is compared
strictly, including the order of inline style declarations.

One difference is expected and allow-listed: generated decks add

    deck-stage>section{font-family:var(--font-body)}

to the head <style>, because the reference never applies Archivo to its slides.
See docs/TEMPLATING-REPORT.md. Exit code 0 means identical modulo that rule.
"""

from __future__ import annotations

import difflib
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

FONT_FIX = "deck-stage>section{font-family:var(--font-body)}"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


def normalise_style(value: str) -> str:
    decls = [d.strip() for d in value.split(";")]
    return ";".join(re.sub(r"\s+", " ", d) for d in decls if d)


class Tokeniser(HTMLParser):
    """Flatten a document into comparable tokens."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tokens: list[str] = []
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        if tag == "style":
            self._in_style = True
        parts = []
        for name, value in sorted(attrs):
            value = "" if value is None else value
            if name == "style":
                value = normalise_style(value)
            else:
                value = re.sub(r"\s+", " ", value).strip()
            parts.append(f"{name}={value!r}")
        self.tokens.append(f"<{tag} " + " ".join(parts) + ">" if parts else f"<{tag}>")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False
        if tag not in VOID:
            self.tokens.append(f"</{tag}>")

    def handle_data(self, data):
        if self._in_style:
            # Strip the allow-listed font rule so the rest of the block still
            # gets compared character for character.
            data = data.replace(FONT_FIX, "")
        text = re.sub(r"\s+", " ", data).strip()
        if text:
            self.tokens.append(f"#text {text!r}")

    def handle_comment(self, data):
        pass  # comments do not render


def tokenise(path: Path) -> list[str]:
    parser = Tokeniser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser.tokens


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    generated, reference = Path(argv[0]), Path(argv[1])
    for path in (generated, reference):
        if not path.is_file():
            print(f"error: no such file: {path}", file=sys.stderr)
            return 2

    got, want = tokenise(generated), tokenise(reference)
    if got == want:
        print(f"identical: {len(got)} tokens match (allow-listed: the font-family fix)")
        return 0

    diff = list(difflib.unified_diff(
        want, got, fromfile=str(reference), tofile=str(generated), lineterm="", n=2
    ))
    print(f"DIFFERS: {len(got)} generated tokens vs {len(want)} reference tokens")
    for line in diff[:400]:
        print(line)
    if len(diff) > 400:
        print(f"... {len(diff) - 400} more diff lines")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
