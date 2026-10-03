#!/usr/bin/env python3
"""Make the light copies of the header's coins and wordmarks.

    python3 scripts/brand.py            # make any copy that is missing or out of date, and record what was made
    python3 scripts/brand.py --check    # change nothing; say which copies are missing or out of date

Every page shows the three coins and the site's wordmark in its header. The originals are PNG files cut from Jim's
renders, about 22 KB a coin and 56 to 76 KB a wordmark, which was more than the page and its stylesheet together.
This script writes the same pictures, at the same size in pixels, as WebP files beside the originals:

    shared/static/brand/<site>-coin.png      ->  shared/static/brand/<site>-coin.webp
    sites/<site>/static/brand/wordmark.png   ->  sites/<site>/static/brand/wordmark.webp

The header and the footer offer the WebP copy first and keep the PNG for a browser that cannot show WebP
(shared/templates/base.html). Nothing is cropped, recolored, or redrawn. The PNG files stay: they are that fallback,
the charts' footer coin and the sats badge on other sites use stats-coin.png, and the sharing cards and the checklist
PDF use wordmark.png.

shared/brand.json records, for each copy, the SHA-256 of the PNG it was made from and of the copy itself. The site
build reads it and offers a copy only while both still match. So when a PNG is replaced and this script has not been
run, the page names the new PNG alone, never the old copy, and the build prints a note. File times are not used,
because git gives every file the time of the checkout.

A copy that is in place and matches its record is left alone, so running this twice changes nothing, whatever version
of Pillow is installed. Run it whenever a coin or a wordmark is replaced, and commit the copies and shared/brand.json
with the originals. Separate from the Daily Build and from the site build. Needs Pillow.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECORD = ROOT / "shared" / "brand.json"
SITES = ("stats", "facts", "acts")
QUALITY = 92          # high enough that the copy cannot be told from the original at the sizes the header shows
AGAIN = "run python3 scripts/brand.py"


def pairs() -> list[tuple[Path, Path]]:
    out = []
    for key in SITES:
        coin = ROOT / "shared" / "static" / "brand" / f"{key}-coin.png"
        word = ROOT / "sites" / key / "static" / "brand" / "wordmark.png"
        out += [(coin, coin.with_suffix(".webp")), (word, word.with_suffix(".webp"))]
    return out


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def name_of(path: Path) -> str:
    """A file's name in the record: its path from the top of the repository, with forward slashes on every system."""
    return path.relative_to(ROOT).as_posix()


def load_record() -> tuple[dict, str | None]:
    """The record as a dict (empty when there is none to use), and what is wrong with the file, if anything."""
    if not RECORD.is_file():
        return {}, "shared/brand.json is missing"
    try:
        record = json.loads(RECORD.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}, "shared/brand.json cannot be read"
    if not isinstance(record, dict):
        return {}, "shared/brand.json is not a record of the header pictures"
    return record, None


def main(argv: list[str]) -> int:
    unknown = [arg for arg in argv if arg != "--check"]
    if unknown:
        print(f"unknown option {unknown[0]}; the only option is --check")
        return 2
    only_check = "--check" in argv
    record, problem = load_record()
    notes = [f"{problem}; {AGAIN}"] if only_check and problem else []
    made: dict[str, dict[str, str]] = {}
    for original, copy in pairs():
        name = name_of(copy)
        if not original.is_file():
            notes.append(f"{name_of(original)} is missing")
            continue
        entry = record.get(name) if isinstance(record.get(name), dict) else None
        if only_check:
            if problem:
                continue                      # the one line about the record says it all
            if not copy.is_file():
                notes.append(f"{name} is missing; {AGAIN}")
            elif entry is None:
                notes.append(f"shared/brand.json has no entry for {name}; {AGAIN}")
            elif entry.get("png") != digest(original):
                notes.append(f"{original.name} has changed since {name} was made from it; {AGAIN}")
            elif entry.get("webp") != digest(copy):
                notes.append(f"{name} is not the copy this script made; {AGAIN}")
            continue
        if copy.is_file() and entry is not None and entry.get("png") == digest(original) and entry.get("webp") == digest(copy):
            made[name] = {"png": entry["png"], "webp": entry["webp"]}
            print(f"  {name:46} in place, left alone")
            continue
        from PIL import Image                 # only needed when a copy has to be made
        with Image.open(original) as picture:
            picture.convert("RGBA").save(copy, "WEBP", quality=QUALITY, alpha_quality=100, method=6)
        made[name] = {"png": digest(original), "webp": digest(copy)}
        print(f"  {name:46} {original.stat().st_size / 1024:6.1f} KB -> {copy.stat().st_size / 1024:5.1f} KB")
    if not only_check:
        text = json.dumps(dict(sorted(made.items())), indent=1) + "\n"
        try:
            same = RECORD.is_file() and RECORD.read_text(encoding="utf-8") == text
        except (OSError, ValueError):
            same = False
        if not same:
            RECORD.write_text(text, encoding="utf-8")
    for note in notes:
        print("NOTE", note)
    if only_check and not notes:
        print(f"{len(pairs())} header pictures: every light copy is in place, and it and its PNG match the record")
    return 1 if notes else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
