"""Programmatic chart pages: content/stats/charts/<slug>.md, one per chart, refreshed every morning.

The Daily Build owns the `chart` and `updated` front matter keys and the text between the
<!-- auto:start --> and <!-- auto:end --> markers. Everything else in the file (the title, the description,
the explainer the Content Writer adds below the markers, extra sources) is kept as it is.
A page that does not exist yet is created with a plain default body.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import yaml

from scripts import series as S

ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = ROOT / "content" / "stats" / "charts"
AUTO_START, AUTO_END = "<!-- auto:start -->", "<!-- auto:end -->"
FRONT = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.S)


def _split(text: str) -> tuple[dict, str]:
    match = FRONT.match(text)
    if not match:
        return {}, text
    return (yaml.safe_load(match.group(1)) or {}), text[match.end():]


def _auto_block(entry: dict) -> str:
    """The paragraph, the small table, and the data line under a chart. The words are Jim's: the finding (the chart's
    title sentence, or the entry's own `lead`), then the entry's `detail` sentence; a `credit` line, when the source's
    terms want one beside the reading; the table under `column`; and the line that links the data file."""
    rows = "\n".join(f"| {label} | {when} | {text} |" for label, when, text in entry["table"])
    unit = entry["unit"]
    column = entry.get("column") or unit[0].upper() + unit[1:]
    lead = entry.get("lead") or f"{entry['title']}."
    paragraph = f"{lead} {entry.get('detail', '')}".strip()
    credit = f"{entry['credit']}\n\n" if entry.get("credit") else ""
    return (
        f"{AUTO_START}\n"
        f"{paragraph}\n\n"
        f"{credit}"
        f"| When | Date | {column} |\n| --- | --- | --- |\n{rows}\n\n"
        f"Download the data behind this chart: [{entry['data_file']}]({entry['data_file']}). There are 100,000,000 sats in one bitcoin.\n"
        f"{AUTO_END}"
    )


def write_page(entry: dict, pulled_text: str, today: dt.date) -> Path:
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    path = PAGES_DIR / f"{entry['slug']}.md"
    if path.exists():
        meta, body = _split(path.read_text(encoding="utf-8"))
    else:
        meta, body = {}, f"{AUTO_START}\n{AUTO_END}\n\n"

    # Keys the build owns
    meta.setdefault("title", entry["heading"])
    meta.setdefault("description", entry["description"])
    meta["template"] = "chart"
    meta["updated"] = today.isoformat()
    meta["chart"] = {
        "slug": entry["slug"],
        "alt": entry["title"],
        "source": ", ".join(s["name"] for s in entry["sources"]),
        "source_links": [{"name": s["name"], "url": s["url"]} for s in entry["sources"]],   # the caption links each source name
        "pulled": pulled_text,
        "data": entry["data_file"],
    }
    meta["attribution"] = entry["attribution"]
    if not meta.get("sources"):
        meta["sources"] = entry["sources"]

    block = _auto_block(entry)
    if AUTO_START in body and AUTO_END in body:
        body = body[: body.index(AUTO_START)] + block + body[body.index(AUTO_END) + len(AUTO_END):]
    else:
        body = block + "\n\n" + body.lstrip()

    front = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=1000).strip()
    path.write_text(f"---\n{front}\n---\n{body.rstrip()}\n", encoding="utf-8")
    return path
