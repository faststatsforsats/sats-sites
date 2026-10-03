"""Read a content page: YAML front matter on top, Markdown below.

A page file looks like this:

    ---
    title: How to buy your first bitcoin
    description: Under 155 characters for search results.
    template: guide            # page | guide | chart | home | route | campaign (default: page; guide for Acts and Facts)
    updated: 2026-10-13
    nav: true                  # top-level pages only: add to the header nav (`first` puts it before the sections)
    nav_label: Network         # short nav name (default: the title)
    understand_first:          # Acts guides only: the Facts explainer behind this guide
      text: What a sat is and why bitcoin is divisible
      url: https://fastfactsforsats.com/basics/what-is-a-sat/
    attribution: [coingecko]   # any of coingecko, fred, bls, altme; adds the required source lines
    sources:
      - name: Kraken fee schedule
        url: https://www.kraken.com/features/fee-schedule
    placements:                # affiliate boxes; slug must be in go/redirects.csv; a box renders only once the status is approved
      - slug: kraken
        headline: Kraken
        text: One sentence on what it is and who it suits.
    live: true                 # optional note that the body uses [[live:...]] figures (see lib/site.py LIVE_TOKEN)
    ---
    The answer in two sentences...

A campaign page (template: campaign) may add:

    eyebrow: October 2026        # small label above the title
    hook_chart:                  # one Stats chart shown under the title; its PNGs are copied from charts/
      slug: twenty-five-a-week
      alt: What $25 a week since 2020 bought in sats
      caption: One sentence under the chart.
      link_text: See the numbers behind the chart   # the words that link to the chart's Stats page

The file's path sets the URL: content/acts/buy/first-bitcoin.md becomes /buy/first-bitcoin/,
content/acts/buy/index.md becomes /buy/, and content/acts/index.md is the home page.

Pages every site carries (the privacy policy, the affiliate disclosure, the terms, the contact page) live once, in
content/shared/, and are built into all three sites at the same address. They sit at the top level (no folders) and
may add:

    footer_label: Privacy        # the page joins the row of links in every footer under this short name
    order: 1                     # position in that row (and in a section's list, for any page)

A file at the same address under content/<site>/ replaces the shared one on that site. Shared pages stay out of the feed.

Three tokens can be written in a page body: [[programs]] (the sentence naming the affiliate programs that are approved
today, for the affiliate disclosure), and on the Stats site [[embed:badge]] and [[embed:chart:<slug>]] (the sats badge
and one chart, shown the way another site would embed them, each with its code). lib/site.py expands them.

A fourth shows an illustration from shared/art.yml: [[art:<name>]] on a line of its own (the picture with its quoted
line as the caption), [[art:<name>:plain]] (the picture alone), or [[art:<name>:bridge]] (the picture, its caption, and
under them its bridge to the next section). The picture must be `approved` in shared/art.yml.

Every key a template prints must have a value: a key left out, left empty, or given the wrong kind of value (a number
in quotes, a word where a list belongs) stops the build with one line that names the page.

Home pages (template: home; Jim's improvement plan, October 2026). Each site's home page has its own first screen,
and its words are in the front matter of content/<site>/index.md, not in the template:

    hero:                        # all three sites
      headline: ...              # the page's one h1
      intro: ...
      button: {text: ..., url: ...}   # the one main action (Stats, Facts)
      note: ...                  # a small line under the button (Stats, where it carries a [[live:...]] figure)
      art: key-and-doorway       # the picture beside the headline (Facts); a name from shared/art.yml

    Stats:  compare (heading, legend, today_label, price_label, dates, dates_today: the words around the
            first-screen comparison; the figures come from lib/stats_data.py), today_heading, stories_heading and
            stories (each: a headline, a url, a button, and either `art`, a picture, or `figure` with its
            `figure_title`, two bars; `take` is the chart's quoted line), converter_heading, converter_more,
            weekly (heading, start, and `charts`: slugs that take turns, one a week, each with its quoted line),
            subscribe.heading (shown once newsletter_embed is set in site.yml)
    Facts:  questions_heading, questions_more, questions (each: question, answer, example, missed, more). A line
            is plain words, or a quote written as {from: /basics/what-is-a-sat/, quote: own-part}: the build pulls
            the passage that page marks with that name (see "Passages a page marks for quoting" below), so the card
            always says what the explainer says and holds no copy of it.
    Acts:   tasks_heading, tasks (name, url, time, need, done, wait, cta), path (the twelve acts: heading, text,
            wait, button, url, key, total, progress_text, progress_label, checklist_text)

A guided route (template: route; the five-minute guide on Facts) is built from other pages' own words:

    more_label: "The full explanation:"
    stop_label: "Question {n} of {total}"    # the small label over each stop
    stops:
      - question: "What is a sat?"
        from: /basics/what-is-a-sat/     # the page quoted
        take: 5                          # its first five blocks (up to its first subhead; a plain number), or
        under: "Why sats matter"         # the blocks under that subhead
    check:                               # an optional knowledge check; nothing a reader picks is stored or sent
      heading, intro, button, show, right, wrong, answer_is ("The answer:"), score ("You got {right} of {total}."),
      unanswered
      questions: [{q: ..., options: [...], answer: 3, why: {quote: latest-trade}}]
                                         # answer: the number of the right option (no quotes); why: plain words, or
                                         # a passage marked on the page the stop with the same number quotes
                                         # (`from` names another page)
    next: {heading: ..., links: [{text: ..., url: ..., note: ...}]}

A chart page (template: chart) may add `question` (the question the chart answers, shown under the title) and `art`
(a picture from shared/art.yml that opens the page, with its quoted line and its bridge to the chart). A campaign page may
add `progress` (key, done_label, count_text, saved_text, label, clear_label): tick boxes on its `ol.acts` list, kept in
the reader's own browser by shared/static/actions.js. `nav: first` puts a top-level page first in the header menu.

Passages a page marks for quoting. A question card on the Facts home page and a reason in the knowledge check show an
explainer's own words. The explainer marks the passage in its Markdown with two comment lines, each on a line of its
own with a blank line either side:

    <!-- quote: key-ring -->

    Think of the wallet as the key ring that lets you use what is yours.

    <!-- /quote: key-ring -->

The marks never reach the page: they are taken out before the text is rendered. Whatever stands between them is what
the card shows, so the words are changed in one place, the explainer. A name is small letters, digits, and hyphens,
and is used once on a page. When a mark is missing the build does not stop: the card goes without that line, and the
build prints a note that names the mark. Keep the marks when an explainer's text is replaced.
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

# A passage marked for quoting: <!-- quote: name --> ... <!-- /quote: name -->, each mark on a line of its own
QUOTE_MARK = re.compile(r"^[ \t]*<!--[ \t]*(/?)quote:[ \t]*([a-z0-9][a-z0-9-]*)[ \t]*-->[ \t]*$", re.M)
QUOTE_LIKE = re.compile(r"^[ \t]*<!--[^\n]*\bquote\b[^\n]*-->[ \t]*$", re.M | re.I)

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
    shared: bool = False          # True for a page from content/shared/, which every site builds
    quotes: dict = field(default_factory=dict)                 # name -> the Markdown of a passage this page marks for quoting
    quote_problems: list[str] = field(default_factory=list)    # marks that do not pair up; the build prints each as a note

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
    def footer_label(self) -> str:
        """Short name for the row of links in every footer; empty when the page is not listed there."""
        return str(self.meta.get("footer_label") or "").strip()

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


def split_quotes(body: str) -> tuple[str, dict, list[str]]:
    """Take the quote marks out of a page's Markdown. Returns the text without them (so the page renders exactly as it
    would with no marks), the marked passages by name, and what is wrong with any mark that does not pair up."""
    marks = [(m.start(), m.end(), m.group(1) == "/", m.group(2)) for m in QUOTE_MARK.finditer(body)]
    quotes: dict[str, str] = {}
    problems: list[str] = []
    used: set[int] = set()
    for i, (start, end, closing, name) in enumerate(marks):
        if closing:
            continue
        j = next((k for k in range(i + 1, len(marks)) if marks[k][2] and marks[k][3] == name and k not in used), None)
        if j is None:
            problems.append(f"the mark <!-- quote: {name} --> has no <!-- /quote: {name} --> after it")
            continue
        used.update((i, j))
        if name in quotes:
            problems.append(f"the name {name!r} marks two passages; the first is the one quoted")
            continue
        passage = QUOTE_MARK.sub("", body[end:marks[j][0]])
        quotes[name] = re.sub(r"\n{3,}", "\n\n", passage).strip()
        if not quotes[name]:
            del quotes[name]
            problems.append(f"the mark <!-- quote: {name} --> has no words between it and its end")
    for i, (start, end, closing, name) in enumerate(marks):
        if closing and i not in used:
            problems.append(f"the mark <!-- /quote: {name} --> has no <!-- quote: {name} --> before it")
    clean = QUOTE_MARK.sub("", body)
    for stray in QUOTE_LIKE.findall(clean):         # looks like a mark and is not one (a capital, a space in the name)
        problems.append(f"{stray.strip()} is not a quote mark the build knows; write <!-- quote: name --> with small letters, digits, and hyphens")
    if marks:
        clean = re.sub(r"\n{3,}", "\n\n", clean)
    return clean, quotes, problems


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
    body, quotes, quote_problems = split_quotes(body)
    url, section = url_for(content_root, source)
    page = Page(source=source, url=url, section=section, meta=meta, body_md=body, quotes=quotes, quote_problems=quote_problems)
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
