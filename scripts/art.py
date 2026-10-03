#!/usr/bin/env python3
"""Make the web copies of the illustrations in shared/art.yml.

    python3 scripts/art.py                 # every picture
    python3 scripts/art.py key-and-doorway # one picture
    python3 scripts/art.py --check         # change nothing; say what is missing or out of date

A picture is a master and its web copies:

    art/masters/<name>.png                 the picture as supplied, landscape 3:2 (never served)
    shared/static/art/<name>-480.webp      the web copies: the whole picture at 480, 768, 1080, and 1536 px wide
    shared/static/art/<name>-768.webp      (a master narrower than a size is not enlarged; that size is its own width)
    shared/static/art/<name>-1080.webp
    shared/static/art/<name>-1536.webp
    shared/static/art/<name>-1080.jpg      for a browser that cannot show WebP

Nothing is cropped. A crop for a thumbnail or a social card is a decision about what the picture means (the hook has
to stay on the gift, the wedge on the plate), so it is made by hand and gets its own entry, not by this script.

To add a picture: save the master as art/masters/<name>.png, add its entry to shared/art.yml (alt text, the
caption, where it goes, where it came from, who may use it, who reviewed it, its status), run this script, and commit
the master, the entry, and the web copies together. The site build then checks that every copy is there.

Separate from the Daily Build and from the site build. Needs Pillow and PyYAML.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MASTERS = ROOT / "art" / "masters"
WEB = ROOT / "shared" / "static" / "art"
WIDTHS = (480, 768, 1080, 1536)      # the same list as ART_WIDTHS in lib/site.py and the srcset in shared/templates/_art.html
FALLBACK = 1080                      # ART_FALLBACK in lib/site.py
WEBP_QUALITY, JPEG_QUALITY = 80, 82


def copies(name: str) -> list[Path]:
    return [WEB / f"{name}-{width}.webp" for width in WIDTHS] + [WEB / f"{name}-{FALLBACK}.jpg"]


def make(name: str, entry: dict) -> list[str]:
    master = MASTERS / f"{name}.png"
    if not master.exists():
        return [f"{name}: art/masters/{name}.png is missing"]
    picture = Image.open(master).convert("RGB")
    width, height = picture.size
    notes = []
    if (entry.get("width"), entry.get("height")) != (width, height):
        notes.append(f"{name}: shared/art.yml says {entry.get('width')} by {entry.get('height')}, the master is {width} by {height}; correct the entry")
    if abs(width / height - 1.5) > 0.01:
        notes.append(f"{name}: the master is not 3:2 ({width} by {height}); the pages lay pictures out at 3:2")
    WEB.mkdir(parents=True, exist_ok=True)
    for target in WIDTHS:
        size = (min(target, width), round(min(target, width) * height / width))
        copy = picture if size == picture.size else picture.resize(size, Image.LANCZOS)
        out = WEB / f"{name}-{target}.webp"
        copy.save(out, "WEBP", quality=WEBP_QUALITY, method=6)
        print(f"  {out.name:46} {size[0]} by {size[1]}  {out.stat().st_size / 1024:6.1f} KB")
    size = (min(FALLBACK, width), round(min(FALLBACK, width) * height / width))
    out = WEB / f"{name}-{FALLBACK}.jpg"
    picture.resize(size, Image.LANCZOS).save(out, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    print(f"  {out.name:46} {size[0]} by {size[1]}  {out.stat().st_size / 1024:6.1f} KB")
    return notes


def check(name: str, entry: dict) -> list[str]:
    master = MASTERS / f"{name}.png"
    if not master.exists():
        return [f"{name}: art/masters/{name}.png is missing"]
    notes = [f"{name}: {path.name} is missing" for path in copies(name) if not path.exists()]
    notes += [f"{name}: {path.name} is older than its master; run python3 scripts/art.py {name}"
              for path in copies(name) if path.exists() and path.stat().st_mtime < master.stat().st_mtime]
    with Image.open(master) as picture:
        if (entry.get("width"), entry.get("height")) != picture.size:
            notes.append(f"{name}: shared/art.yml says {entry.get('width')} by {entry.get('height')}, the master is {picture.size[0]} by {picture.size[1]}")
    return notes


def main(argv: list[str]) -> int:
    registry = yaml.safe_load((ROOT / "shared" / "art.yml").read_text(encoding="utf-8")) or {}
    only_check = "--check" in argv
    names = [arg for arg in argv if not arg.startswith("--")] or list(registry)
    notes = []
    for name in names:
        if name not in registry:
            notes.append(f"{name}: shared/art.yml has no entry by that name")
            continue
        if not only_check:
            print(name)
        notes += (check if only_check else make)(name, registry[name])
    for note in notes:
        print("NOTE", note)
    if only_check and not notes:
        print(f"{len(names)} pictures: every master and web copy is in place")
    return 1 if notes else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
