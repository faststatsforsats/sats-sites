"""Read a content page: YAML front matter on top, Markdown below.

A page file looks like this:

    ---
    title: How to buy your first bitcoin
    description: Under 155 characters for search results.
    template: guide            # page | guide | chart | home (default: page; guide for Acts and Facts)
    updated: 2026-10-13
    nav: true                  # top-level pages only: add to the header nav
    nav_label: Network         # short nav name (default: the title)
    understand_first:          # Acts guides only: the Facts explainer behind this guide
      text: What a sat is and why bitcoin is divisible
      url: https://fastfactsforsats.com/basics/what-is-a-sat/
    attribution: [coingecko]   # any of coingecko, fred, bls, altme; adds the required source lines
    sources:
      - name: Kraken fee schedule
        url: https://www.kraken.com/features/fee-schedule
    placements:                # affiliate boxes; slug must be in go/redirects.csv; a box renders only once the status is approved
    live: true                 # optional note that the body uses [[live:...]] figures (see lib/site.py LIVE_TOKEN)
      - slug: kraken
        headline: Kraken
        text: One sentence on what it is and who it suits.
    ---
    The answer in two sentences...

The file's path sets the URL: content/acts/buy/first-bitcoin.md becomes /buy/first-bitcoin/,
content/acts/buy/index.md becomes /buy/, and content/acts/index.md is the home page.
"""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import markdown
import yaml

FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.S)
GO_LINK = re.compile(r"/go/([A-Za-z0-9][A-Za-z0-9_-]*)/?")

MD_EXTENSIONS = ["tables", "fenced_code", "attr_list", "toc", "md_in_html", "sane_lists"]
MD_CONFIG = {"toc": {"permalink": False, "toc_depth": "2-3"}}


@dataclass
class Page:
    source: Path
    url: str                      # /buy/first-bitcoin/
    section: str                  # buy ("" for top-level pages)
    meta: dict
    body_md: str
    body_html: str = ""
    toc_html: str = ""
    go_slugs: list[str] = field(default_factory=list)          # /go/ links written in the body (must be approved)
    placement_slugs: list[str] = field(default_factory=list)   # placement boxes; they render only once the program is approved

    @property
    def title(self) -> str:
        return str(self.meta.get("title", "")).strip()

    @property
    def template(self) -> str:
        return str(self.meta.get("template") or ("home" if self.url == "/" else "page"))

    @property
    def updated(self) -> _dt.date | None:
        value = self.meta.get("updated")
        if isinstance(value, _dt.datetime):
            return value.date()
        if isinstance(value, _dt.date):
            return value
        if isinstance(value, str) and value.strip():
            return _dt.date.fromisoformat(value.strip()[:10])
        return None

    @property
    def is_draft(self) -> bool:
        return bool(self.meta.get("draft", False)) or self.meta.get("published") is False

    @property
    def in_nav(self) -> bool:
        return bool(self.meta.get("nav", False))

    @property
    def nav_label(self) -> str:
        """Short name for the header nav; falls back to the title."""
        return str(self.meta.get("nav_label") or self.title)

    @property
    def out_path(self) -> str:
        return "index.html" if self.url == "/" else self.url.strip("/") + "/index.html"


def split_front_matter(text: str) -> tuple[dict, str]:
    match = FRONT_MATTER.match(text)
    if not match:
        return {}, text
    meta = yaml.safe_load(match.group(1)) or {}
    if not isinstance(meta, dict):
        raise ValueError("front matter must be a mapping")
    return meta, text[match.end():]


def url_for(content_root: Path, source: Path) -> tuple[str, str]:
    """Return (url, section) for a Markdown file under content_root."""
    rel = source.relative_to(content_root).with_suffix("")
    parts = list(rel.parts)
    section = parts[0] if len(parts) > 1 else ""   # a file inside a folder belongs to that section
    if parts[-1] == "index":
        parts = parts[:-1]
    url = "/" + "/".join(parts) + ("/" if parts else "")
    return url, section


def render_markdown(body_md: str) -> tuple[str, str]:
    md = markdown.Markdown(extensions=MD_EXTENSIONS, extension_configs=MD_CONFIG, output_format="html5")
    html = md.convert(body_md)
    toc = getattr(md, "toc", "") or ""
    # python-markdown wraps the TOC in <div class="toc">; an empty TOC is just that wrapper
    if "<li>" not in toc:
        toc = ""
    return html, toc


def load_page(content_root: Path, source: Path) -> Page:
    text = source.read_text(encoding="utf-8")
    meta, body = split_front_matter(text)
    url, section = url_for(content_root, source)
    page = Page(source=source, url=url, section=section, meta=meta, body_md=body)
    page.body_html, page.toc_html = render_markdown(body)
    page.go_slugs = sorted(set(GO_LINK.findall(body)))
    page.placement_slugs = [str(pl.get("slug", "")).strip() for pl in (meta.get("placements") or []) if str(pl.get("slug", "")).strip()]
    return page


def load_pages(content_root: Path) -> list[Page]:
    pages = []
    for source in sorted(content_root.rglob("*.md")):
        if source.name.startswith("_") or source.name == "README.md":
            continue
        pages.append(load_page(content_root, source))
    return pages
