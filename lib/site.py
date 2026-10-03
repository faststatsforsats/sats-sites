"""Build one site: content/<site>/*.md + shared templates -> sites/<site>/dist/

Run from the repository root:  python3 build.py stats     (or facts, acts, all)
Cloudflare Pages runs the same command for each project; see README.md, "Cloudflare Pages settings".
"""

from __future__ import annotations

import re

import datetime as _dt
import hashlib
import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from jinja2.exceptions import UndefinedError

from markupsafe import Markup

from .content import Page, load_pages, render_markdown
from .redirects import load_redirects, render_redirects_file
from .stats_data import WITHDRAWN_DATA, StatsData

ROOT = Path(__file__).resolve().parent.parent
SITE_KEYS = ("stats", "facts", "acts")

# The credit line each data source gets in the footer of a page that shows its data. The wording of the CoinGecko,
# FRED, and BLS lines is fixed by those providers' terms; do not edit it without reading the terms again.
# "link" is the part of the line that carries the link: the provider's name.
ATTRIBUTION_LINES = {
    "coingecko": {"text": "Data provided by CoinGecko", "link": "CoinGecko", "url": "https://www.coingecko.com"},
    "fred": {"text": "This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis.", "link": "FRED", "url": "https://fred.stlouisfed.org"},
    "bls": {"text": "Source: U.S. Bureau of Labor Statistics, retrieved {date}. BLS.gov cannot vouch for the data or analyses derived from these data after the data have been retrieved from BLS.gov.", "link": "U.S. Bureau of Labor Statistics", "url": "https://www.bls.gov"},
    "altme": {"text": "Source: alternative.me", "link": "alternative.me", "url": "https://alternative.me/crypto/fear-and-greed-index/"},
    "mempool": {"text": "Fee data: mempool.space", "link": "mempool.space", "url": "https://mempool.space"},
    "blockchain": {"text": "Price and network data: blockchain.com", "link": "blockchain.com", "url": "https://www.blockchain.com/explorer/charts"},
    "worldbank": {"text": "Gold price: World Bank Commodity Price Data (The Pink Sheet), CC BY 4.0", "link": "World Bank Commodity Price Data (The Pink Sheet)", "url": "https://www.worldbank.org/en/research/commodity-markets"},
}


def credit_lines(codes, today) -> list[dict]:
    """Footer credit lines for the given source codes, each split around the provider's name so only the name is linked."""
    lines = []
    for code in codes:
        line = ATTRIBUTION_LINES[str(code)]
        text = line["text"].format(date=long_date(today))
        before, _, after = text.partition(line["link"])
        lines.append({"text": text, "before": before, "link": line["link"], "after": after, "url": line["url"]})
    return lines

SATS_LINE = "Sats means satoshis, the smallest unit of bitcoin."
DISCLOSURE_LINE = "Some links here are affiliate links. If you buy through them, this site earns a commission at no cost to you."

# The templates that print the disclosure line above a /go/ link written in a page body. The affiliate disclosure
# page tells readers that a page with affiliate links always shows that line, so a body link anywhere else is an error.
DISCLOSING_TEMPLATES = {"page", "guide", "chart", "campaign"}

# [[programs]] on the affiliate disclosure page: the programs whose status is approved in go/redirects.csv, as of the
# day of the build. The three sentences are drafted for Jim's review; change them with him.
PROGRAMS_TOKEN = "[[programs]]"
PROGRAMS_NONE = "As of {date}, no program is active, so no link on these sites pays a commission."
PROGRAMS_ONE = "As of {date}, one program is active: {names}."
PROGRAMS_MANY = "As of {date}, the active programs are {names}."

# [[embed:badge]] and [[embed:chart:<slug>]]: the sats badge and one chart, shown the way another site would embed
# them, each with its code (shared/templates/_embed_badge.html and _embed_chart.html). A token on a line of its own
# arrives from Markdown wrapped in a paragraph; the whole paragraph is replaced.
EMBED_TOKEN = re.compile(r"(?:<p>\s*)?\[\[embed:(badge|chart)(?::([a-z0-9-]+))?\]\](?:\s*</p>)?")

# [[art:<name>]] on a line of its own: one of the illustrations in shared/art.yml, with its caption (the quoted line) under it.
# [[art:<name>:plain]] shows the picture alone; [[art:<name>:inset]] keeps it narrower than the text column, so the
# picture can open a page without pushing what follows off the screen.
ART_TOKEN = re.compile(r"(?:<p>\s*)?\[\[art:([a-z0-9-]+)((?::[a-z]+)*)\]\](?:\s*</p>)?")
ART_WIDTHS = (480, 768, 1080, 1536)     # the web copies of every picture, in shared/static/art/
ART_FALLBACK = 1080                     # and the one JPEG
ART_STATUSES = ("approved", "prepared")   # prepared: the web copies exist, no page shows it yet


def load_art(report) -> dict:
    """shared/art.yml, checked: every picture it names has its web copies, its alt text, and its size."""
    path = ROOT / "shared" / "art.yml"
    registry = (load_yaml(path) or {}) if path.exists() else {}
    folder = ROOT / "shared" / "static" / "art"
    if not isinstance(registry, dict):
        report.error("shared/art.yml: expected one entry per picture (name: then its fields)")
        return {}
    for name in [name for name, entry in registry.items() if not isinstance(entry, dict)]:
        report.error(f"shared/art.yml: {name} has no fields; give it alt, width, height, and status")
        del registry[name]
    for name, entry in registry.items():
        for key in ("alt", "width", "height"):
            if not entry.get(key):
                report.error(f"shared/art.yml: {name} needs {key}")
                entry.setdefault(key, "" if key == "alt" else 0)       # so the page that uses it still renders and the error above is what is seen
        missing = [f"{name}-{w}.webp" for w in ART_WIDTHS if not (folder / f"{name}-{w}.webp").exists()]
        if not (folder / f"{name}-{ART_FALLBACK}.jpg").exists():
            missing.append(f"{name}-{ART_FALLBACK}.jpg")
        if missing:
            report.error(f"shared/art.yml: {name} has no web copy {', '.join(missing)} in shared/static/art/")
        for where in em_dashes(entry):
            report.error(f"shared/art.yml: {name} {where} contains an em dash; use a comma, colon, semicolon, or period")
        if entry.get("status") not in ART_STATUSES:
            report.error(f"shared/art.yml: {name} needs a status, one of {', '.join(ART_STATUSES)}")
    return registry


def art_ready(art: dict, name: str, page, report) -> bool:
    """A page may show a picture only once shared/art.yml lists it as approved (Jim has looked at it in its place)."""
    entry = art.get(name)
    if entry is None:
        report.error(f"{page.source}: names the picture {name!r}, which shared/art.yml does not list")
        return False
    if entry.get("status") != "approved":
        report.error(f"{page.source}: the picture {name!r} has status {entry.get('status')!r} in shared/art.yml; a page may show a picture only once it is approved")
        return False
    return True


def _blocks(markdown_text: str) -> list[str]:
    """A page body as its blocks (paragraphs, headings, lists, tables), split at blank lines."""
    return [block.strip() for block in re.split(r"\n\s*\n", markdown_text.strip()) if block.strip()]


def excerpt_markdown(page: Page, under: str | None = None, take: int | None = None) -> str | None:
    """Words lifted from another page exactly as that page has them: its opening blocks (up to its first subhead), or
    the blocks under one of its subheads. `take` caps the number of blocks. None when the subhead is not there."""
    blocks = _blocks(page.body_md)
    if under:
        wanted = under.strip().lower()
        start = next((i for i, block in enumerate(blocks) if block.startswith("#") and block.lstrip("#").strip().lower() == wanted), None)
        if start is None:
            return None
        blocks = blocks[start + 1:]
    picked = []
    for block in blocks:
        if block.startswith("#"):
            break
        if block.startswith("[[art:") or block.startswith("<!--"):
            continue
        picked.append(block)
        if take and len(picked) >= take:
            break
    return "\n\n".join(picked) if picked else None


def _plain(text: str) -> str:
    """Text reduced for comparing a quoted sentence with its source: links to their words, emphasis marks and extra spaces dropped."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`]", "", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class Report:
    site: str
    pages: int = 0
    go_pages: int = 0             # /go/<slug>/ "not live" pages, counted apart from the site's pages
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)      # worth a line in the log, never a reason to stop, even with --strict

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)


def _xml(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def programs_sentence(redirects, today) -> str:
    """The sentence [[programs]] stands for: which affiliate programs are approved today (each program once, however many links it has)."""
    names = sorted({target.program for target in redirects.values() if target.approved and target.program}, key=str.lower)
    date = long_date(today)
    if not names:
        return PROGRAMS_NONE.format(date=date)
    if len(names) == 1:
        return PROGRAMS_ONE.format(date=date, names=_xml(names[0]))
    listed = " and ".join(names) if len(names) == 2 else ", ".join(names[:-1]) + ", and " + names[-1]
    return PROGRAMS_MANY.format(date=date, names=_xml(listed))


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def long_date(value) -> str:
    """October 1, 2026 (portable; strftime's %-d is not available everywhere)."""
    return f"{value:%B} {value.day}, {value.year}" if value else ""


def static_url(name: str) -> str:
    """The address of a file in shared/static/ with a short fingerprint of its contents: /static/site.css?v=1a2b3c4d.
    Browsers keep /static/ files for a day (shared/_headers); the fingerprint changes when the file does, so a reader
    who was here yesterday gets today's stylesheet with today's page, not yesterday's."""
    digest = hashlib.sha256((ROOT / "shared" / "static" / name).read_bytes()).hexdigest()[:8]
    return f"/static/{name}?v={digest}"


EM_DASH = "\u2014"


def strings_in(value, where: str = ""):
    """Every string inside a piece of front matter or a settings file, with the path to it: ("hero.intro", "...")."""
    if isinstance(value, str):
        yield where, value
    elif isinstance(value, dict):
        for key, inner in value.items():
            yield from strings_in(inner, f"{where}.{key}" if where else str(key))
    elif isinstance(value, (list, tuple)):
        for number, inner in enumerate(value, start=1):
            yield from strings_in(inner, f"{where}[{number}]")


def em_dashes(value) -> list[str]:
    """Where a piece of front matter or a settings file holds an em dash (the style guide allows none)."""
    return [where for where, text in strings_in(value) if EM_DASH in text]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def brand_record() -> tuple[dict | None, str | None]:
    """shared/brand.json (written by scripts/brand.py) as a dict. When it is missing or cannot be used: None, and one
    line for the build log."""
    path = ROOT / "shared" / "brand.json"
    then = "the header shows the PNG pictures until python3 scripts/brand.py is run"
    if not path.is_file():
        return None, f"shared/brand.json is missing; {then}"
    try:
        record = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None, f"shared/brand.json cannot be read; {then}"
    if not isinstance(record, dict):
        return None, f"shared/brand.json is not a record of the header pictures; {then}"
    return record, None


def png_size(path: Path) -> tuple[int, int] | None:
    """A PNG's width and height in pixels, read from its header (no image library needed at build time)."""
    try:
        with path.open("rb") as handle:
            head = handle.read(24)
    except OSError:
        return None
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


def _never_none(value):
    """A template may not print an empty value: a front matter key left blank (`heading:`) would put the word "None"
    on the page. Raising here turns it into the same one-line error as a missing key."""
    if value is None:
        raise UndefinedError("a word the template prints is empty (a front matter key with nothing after the colon?)")
    return value


def jinja_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(ROOT / "shared" / "templates")),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        finalize=_never_none,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["date"] = long_date
    env.filters["isodate"] = lambda value: value.isoformat() if value else ""
    env.globals["static_url"] = static_url
    return env


def copy_tree(src: Path, dst: Path, skip_names: set[str] | None = None) -> int:
    if not src.exists():
        return 0
    count = 0
    for path in src.rglob("*"):
        if path.is_dir() or path.name in (skip_names or set()):
            continue
        target = dst / path.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        count += 1
    return count


LIVE_TOKEN = re.compile(r"\[\[live:([a-z0-9-]+)((?::[^\]:]+)*)\]\]")
HALVING_INTERVAL = 210_000


def mined_supply(height: int) -> float:
    """Bitcoin issued by the block subsidy through this height (block 0 included)."""
    total, subsidy, blocks = 0.0, 50.0, height + 1
    while blocks > 0:
        n = min(blocks, HALVING_INTERVAL)
        total += n * subsidy
        blocks -= n
        subsidy /= 2
    return total


def expand_live(html: str, stats, report, page) -> str:
    """Replace [[live:key(:arg)*]] tokens in a page body with the baked figure wrapped for live.js.

    Keys: sats-per-dollar, price[:cur], sats-for:amount[:cur], money-for:sats[:cur], fee[:fast|medium|slow], height, to-halving, supply,
    when[:fees] (the price or fee feed's time stamp), cpi, gold (the last monthly figures, not live),
    items (how many everyday items the basket holds; baked, not live)."""
    from .stats_data import CURRENCIES, fmt_money, fmt_sats, month_name

    def missing(key: str) -> str:
        report.warn(f"{page.source}: [[live:{key}]] has no figure yet (the Daily Build has not written data/latest.json)")
        return "<span class=\"live\">(figure arrives with the first Daily Build)</span>"

    def repl(match):
        key, raw = match.group(1), match.group(2)
        args = [a for a in raw.split(":") if a]
        ok = stats is not None and stats.available
        if key == "sats-per-dollar":
            if not ok or not stats.sats_per_dollar:
                return missing(key)
            return f'<span class="live" data-live="sats-per-dollar">{stats.sats_per_dollar:,} sats</span>'
        if key == "price":
            cur = (args[0] if args else "usd").lower()
            price = stats.prices.get(cur) if ok else None
            if not price:
                return missing(key)
            symbol = CURRENCIES.get(cur, {}).get("symbol", cur.upper() + " ")
            return f'<span class="live" data-live="price" data-currency="{cur}">{fmt_money(price, symbol)}</span>'
        if key == "sats-for":
            amount = float(args[0]) if args else 100.0
            cur = (args[1] if len(args) > 1 else "usd").lower()
            price = stats.prices.get(cur) if ok else None
            if not price:
                return missing(key)
            return f'<span class="live" data-live="sats-for" data-amount="{amount:g}" data-currency="{cur}">{fmt_sats(amount / price * 1e8)}</span>'
        if key == "money-for":
            sats = float(args[0]) if args else 100_000.0
            cur = (args[1] if len(args) > 1 else "usd").lower()
            price = stats.prices.get(cur) if ok else None
            if not price:
                return missing(key)
            symbol = CURRENCIES.get(cur, {}).get("symbol", cur.upper() + " ")
            return f'<span class="live" data-live="money-for" data-sats="{sats:g}" data-currency="{cur}">{fmt_money(sats / 1e8 * price, symbol)}</span>'
        if key == "fee":
            tier = args[0] if args else "medium"
            value = (stats.fees or {}).get(tier) if ok else None
            if value is None:
                return missing(key)
            return f'<span class="live" data-live="fees" data-tier="{tier}">{value:g} sat/vB</span>'
        if key == "height":
            height = (stats.fees or {}).get("height") if ok else None
            if not height:
                return missing(key)
            return f'<span class="live" data-live="height">{int(height):,}</span>'
        if key == "to-halving":
            height = (stats.fees or {}).get("height") if ok else None
            if not height:
                return missing(key)
            next_block = (int(height) // HALVING_INTERVAL + 1) * HALVING_INTERVAL
            return f'<span class="live" data-live="to-halving">{next_block - int(height):,}</span>'
        if key == "supply":
            height = (stats.fees or {}).get("height") if ok else None
            if not height:
                return missing(key)
            return f'<span class="live" data-live="supply">{mined_supply(int(height)) / 1e6:.2f} million</span>'
        if key == "when":
            if not ok:
                return missing(key)
            feed = "fees" if args and args[0] == "fees" else "price"
            return f'<span class="live-when" data-live-when="{feed}">as of {stats.updated_text}</span>'
        if key == "cpi":
            cpi = stats.cpi if ok else None
            if not cpi:
                return missing(key)
            return f'{cpi["value"]:.1f} ({month_name(cpi["period"] + "-01")})'
        if key == "gold":
            if not ok or not stats.gold:
                return missing(key)
            day, usd = stats.gold[-1]
            return f'{fmt_money(usd)} an ounce ({month_name(day)})'
        if key == "items":
            count = len(stats.basket()) if ok else 0
            return str(count) if count else missing(key)
        report.error(f"{page.source}: unknown live token [[live:{key}]]")
        return match.group(0)

    return LIVE_TOKEN.sub(repl, html)


def build_site(key: str, out_dir: Path | None = None, strict: bool = False) -> Report:
    if key not in SITE_KEYS:
        raise SystemExit(f"unknown site {key!r}; choose one of {', '.join(SITE_KEYS)} or all")

    report = Report(site=key)
    site_dir = ROOT / "sites" / key
    site = load_yaml(site_dir / "site.yml")
    sites = load_yaml(ROOT / "shared" / "sites.yml")
    redirects = load_redirects(ROOT / "go" / "redirects.csv")
    content_root = ROOT / "content" / key
    dist = out_dir or (site_dir / "dist")
    today = _dt.date.today()

    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)

    pages = [page for page in load_pages(content_root) if not page.is_draft]
    if not any(page.url == "/" for page in pages):
        report.error(f"content/{key}/index.md is missing; every site needs a home page")

    # Pages every site carries (privacy, affiliate disclosure, terms, contact) live once, in content/shared/.
    # A page of the site's own at the same address wins.
    shared_root = ROOT / "content" / "shared"
    own_urls = {page.url for page in pages}
    for page in (load_pages(shared_root) if shared_root.exists() else []):
        if page.is_draft or page.url in own_urls:
            continue
        page.shared = True
        if page.section:
            report.error(f"{page.source}: a shared page sits at the top level of content/shared/, not in a folder")
            continue
        pages.append(page)

    # Validate pages
    seen: dict[str, Page] = {}
    for page in pages:
        if page.url in seen:
            report.error(f"{page.source}: URL {page.url} is also produced by {seen[page.url].source}")
        seen[page.url] = page
        if not page.title:
            report.error(f"{page.source}: front matter needs a title")
        description = str(page.meta.get("description", "")).strip()
        if not description:
            report.warn(f"{page.source}: no description (search results show it; keep it under 155 characters)")
        elif len(description) > 155:
            report.warn(f"{page.source}: description is {len(description)} characters; keep it under 155")
        if len(page.title) > 60:
            report.warn(f"{page.source}: title is {len(page.title)} characters; keep the meta title under 60")
        if page.section and page.section not in (site.get("sections") or {}):
            report.error(f"{page.source}: folder {page.section!r} is not a section in sites/{key}/site.yml")
        for slug in page.go_slugs:
            if slug not in redirects:
                report.error(f"{page.source}: links to /go/{slug} but go/redirects.csv has no such slug")
            elif not redirects[slug].approved:
                report.warn(f"{page.source}: /go/{slug} ({redirects[slug].program}) has status {redirects[slug].status!r}; the style guide allows affiliate links only for approved programs")
        for slug in page.placement_slugs:
            if slug not in redirects:
                report.error(f"{page.source}: placement {slug!r} is not in go/redirects.csv")
        if page.go_slugs and page.template not in DISCLOSING_TEMPLATES:
            report.error(f"{page.source}: template {page.template!r} has no place for the disclosure line above a /go/ link; "
                         f"use a placement box, or one of the templates {sorted(DISCLOSING_TEMPLATES)}")
        if key == "acts" and page.template == "guide" and not page.meta.get("understand_first"):
            report.warn(f"{page.source}: an Acts guide opens with an \"Understand first\" line; add understand_first to the front matter")
        if EM_DASH in page.body_md or EM_DASH in page.title:
            report.error(f"{page.source}: contains an em dash; use a comma, colon, semicolon, or period")
        for where in em_dashes(page.meta):       # a home page's words live in its front matter
            report.error(f"{page.source}: front matter {where} contains an em dash; use a comma, colon, semicolon, or period")

    # Navigation: sections that have at least one page, in site.yml order
    sections = site.get("sections") or {}
    section_pages: dict[str, list[Page]] = {name: [] for name in sections}
    for page in pages:
        if page.section:
            section_pages[page.section].append(page)
    # (a top-level page joins the nav with `nav: true`, after the sections, or `nav: first`, ahead of them)
    top_level = [page for page in pages if page.in_nav and not page.section and page.url != "/"]
    nav = [{"label": page.nav_label, "url": page.url} for page in top_level if page.meta.get("nav") == "first"]
    nav += [{"label": label, "url": f"/{name}/"} for name, label in sections.items() if section_pages.get(name)]
    nav += [{"label": page.nav_label, "url": page.url} for page in top_level if page.meta.get("nav") != "first"]

    # Every site reads data/ and charts/ at build time: Stats builds pages from them, Facts and Acts bake
    # the figures behind [[live:...]] tokens (the browser refreshes those from the API through live.js)
    stats = StatsData(ROOT)
    if stats.available and key == "stats":
        for item in site.get("nav_generated") or []:
            nav.append({"label": item["label"], "url": item["url"]})

    def described(url: str, text: str) -> str:
        """The description a generated page hands to the head (base.html reads page_description), held to the same rules as a written one."""
        if len(text) > 155:
            report.warn(f"{url}: description is {len(text)} characters; keep it under 155")
        if "\u2014" in text:
            report.error(f"{url}: description contains an em dash; use a comma, colon, semicolon, or period")
        return text

    # The row of links in every footer: pages that carry footer_label, in their order
    footer_pages = sorted((page for page in pages if page.footer_label), key=lambda p: (p.meta.get("order", 999), p.footer_label))
    footer_links = [{"label": page.footer_label, "url": page.url} for page in footer_pages]

    env = jinja_env()
    art = load_art(report)
    art_macros = env.get_template("_art.html").module
    by_url = {page.url: page for page in pages}

    def expand_art(html: str, page) -> str:
        """Replace [[art:<name>]] with the picture and its caption."""
        def repl(match):
            name, flags = match.group(1), {flag for flag in match.group(2).split(":") if flag}
            if not art_ready(art, name, page, report):
                return match.group(0)
            # a picture above the page's first subhead is near the top of the screen: it loads at once; later ones wait
            near_top = "<h2" not in html[:match.start()]
            unknown = flags - {"plain", "inset", "bridge"}
            if unknown:
                report.error(f"{page.source}: [[art:{name}]] has an option the build does not know ({', '.join(sorted(unknown))}); use plain, inset, or bridge")
            return str(art_macros.figure(name, art[name], caption="plain" not in flags, cls="art-inset" if "inset" in flags else "", eager=near_top, bridge="bridge" in flags))
        html = ART_TOKEN.sub(repl, html)
        # anything that still looks like a picture token (a typo in the name, a capital, a space, a missing bracket)
        for leftover in re.findall(r"\[+\s*art\w*\s*:[^\]<]*\]*", html, flags=re.I):
            report.error(f"{page.source}: {leftover.strip()} is not a picture token the build knows; write [[art:<name>]] with a name from shared/art.yml (small letters, digits, hyphens)")
        return html

    def excerpt(page, spec) -> Markup:
        """A stop on a guided route: words quoted from another page of this site, rendered with this page's live figures."""
        source = by_url.get(str(spec.get("from", "")))
        if source is None:
            report.error(f"{page.source}: quotes {spec.get('from')!r}, which is not a page of this site")
            return Markup("")
        take = spec.get("take")
        if take is not None and (not isinstance(take, int) or isinstance(take, bool) or take < 1):
            report.error(f"{page.source}: a stop's `take` must be a whole number of blocks (a plain number, no quotes), not {take!r}")
            return Markup("")
        text = excerpt_markdown(source, under=spec.get("under"), take=take)
        if text is None:
            report.error(f"{page.source}: {source.source} has no words to quote" + (f" under the subhead {spec.get('under')!r}" if spec.get("under") else ""))
            return Markup("")
        html, _toc = render_markdown(text)
        return Markup(expand_live(html, stats, report, page))

    def quoted(page, spec, what, default_from=None, within=None) -> Markup | None:
        """Words another page marks for quoting (lib/content.py, "Passages a page marks for quoting"), pulled as that
        page has them today and rendered with this page's live figures; no copy is kept, so an edit to the explainer
        is an edit to the card. None when they cannot be pulled. A mark that is missing is a note, never a reason to
        stop a build: the card or the check goes without that line. A page that does not exist is an error."""
        source_url = str(spec.get("from") or default_from or "")
        source = by_url.get(source_url)
        if source is None:
            report.error(f"{page.source}: {what} quotes {source_url!r}, which is not a page of this site")
            return None
        name = str(spec.get("quote") or "").strip()
        if not name:
            report.error(f"{page.source}: {what} names a page and no passage; write plain words, or {{from: {source_url}, quote: <the name the passage is marked with>}}")
            return None
        passage = source.quotes.get(name)
        if not passage:
            report.note(f"{page.source}: {what} quotes the passage marked {name!r} on {source.source}, which has no such mark, so that line is left out; put <!-- quote: {name} --> before the passage and <!-- /quote: {name} --> after it")
            return None
        if within is not None and _plain(passage) not in _plain(within):
            report.note(f"{page.source}: {what} quotes the passage marked {name!r} on {source.source}, which is not among the words the stop above it shows")
        return inline(page, " ".join(_blocks(passage)))

    def inline(page, text) -> Markup:
        """A line of front matter as HTML: Markdown links and emphasis, and the [[live:...]] figures."""
        html, _toc = render_markdown(str(text))
        html = re.sub(r"^<p>(.*)</p>$", r"\1", html.strip(), flags=re.S) if html.count("<p>") == 1 else html
        return Markup(expand_live(html, stats, report, page))

    for where in em_dashes(site):
        report.error(f"sites/{key}/site.yml: {where} contains an em dash; use a comma, colon, semicolon, or period")
    for where in em_dashes(sites):
        report.error(f"shared/sites.yml: {where} contains an em dash; use a comma, colon, semicolon, or period")
    wordmark = png_size(site_dir / "static" / "brand" / "wordmark.png")
    if wordmark is None:
        report.warn(f"sites/{key}/static/brand/wordmark.png is missing or is not a PNG; the header shows no logo size")
    # The header's coins and wordmark each have a light WebP copy beside the PNG (scripts/brand.py). shared/brand.json
    # records, for each copy, the SHA-256 of the PNG it was made from and of the copy itself. A copy is offered only
    # while it is there and both still match; otherwise the page names the PNG alone and the build prints a note.
    # A note never stops a build, strict or not: the cost of a copy that cannot be offered is weight, nothing else.
    # A coin's PNG that is missing is another matter, since every page names it, so that is a warning.
    for entry in sites:
        if not (ROOT / "shared" / "static" / "brand" / f"{entry['key']}-coin.png").is_file():
            report.warn(f"shared/static/brand/{entry['key']}-coin.png is missing; the header and the footer name it, so they would show a broken picture")
    record, record_note = brand_record()
    if record_note:
        report.note(record_note)

    def light_copy(png: Path) -> bool:
        copy = png.with_suffix(".webp")
        name = copy.relative_to(ROOT).as_posix()
        if record is None or not png.is_file():
            return False
        then = "so the header shows the PNG; run python3 scripts/brand.py"
        if not copy.is_file():
            report.note(f"{name} is missing, so the header shows the PNG, which is about three times the size; run python3 scripts/brand.py")
            return False
        made = record.get(name)
        if not isinstance(made, dict):
            report.note(f"shared/brand.json has no entry for {name}, {then}")
            return False
        if made.get("png") != file_sha256(png):
            report.note(f"{png.name} has changed since {name} was made from it, {then}")
            return False
        if made.get("webp") != file_sha256(copy):
            report.note(f"{name} is not the copy scripts/brand.py made, {then}")
            return False
        return True

    light = {"wordmark": light_copy(site_dir / "static" / "brand" / "wordmark.png"),
             "coins": {entry["key"]: light_copy(ROOT / "shared" / "static" / "brand" / f"{entry['key']}-coin.png") for entry in sites}}

    common = {
        "art": art,
        "pages_by_url": by_url,
        "wordmark": {"width": wordmark[0], "height": wordmark[1]} if wordmark else None,
        "light": light,
        "site": site,
        "sites": sites,
        "sister_sites": [entry for entry in sites if entry["key"] != key],
        "nav": nav,
        "footer_links": footer_links,
        "stats": stats,
        "sats_line": SATS_LINE,
        "disclosure_line": DISCLOSURE_LINE,
        "build_date": today,
        "year": today.year,
    }
    stats_site = next(entry for entry in sites if entry["key"] == "stats")   # the embeds always load from the Stats site

    def expand_embeds(html: str, page) -> str:
        """Replace [[embed:badge]] and [[embed:chart:<slug>]] with the live embed and its code."""
        def repl(match):
            kind, slug = match.group(1), match.group(2)
            if not (stats and stats.available):
                report.warn(f"{page.source}: [[embed:{kind}]] has nothing to show yet (the Daily Build has not written data/ and charts/)")
                return "<p>Conversion data is temporarily unavailable. Please check again later.</p>"
            if kind == "badge":
                return env.get_template("_embed_badge.html").render(stats_site=stats_site, **common)
            card = next((c for c in stats.gallery() if c.get("slug") == slug), None)
            if card is None:
                report.error(f"{page.source}: [[embed:chart:{slug}]] names a chart that charts/index.json does not list")
                return match.group(0)
            return env.get_template("_embed_chart.html").render(stats_site=stats_site, card=card, **common)
        return EMBED_TOKEN.sub(repl, html)

    # Section index pages that have no index.md of their own
    for name, label in sections.items():
        listed = sorted(section_pages.get(name, []), key=lambda p: (p.meta.get("order", 999), p.title))
        if listed and f"/{name}/" not in seen:
            section_description = str((site.get("section_descriptions") or {}).get(name, "")).strip()
            html = env.get_template("section.html").render(
                page=None, title=label, section=name, canonical=site["url"].rstrip("/") + f"/{name}/",
                listed=[p for p in listed if p.url != f"/{name}/"],
                attribution=credit_lines(["blockchain", "bls", "fred", "worldbank", "altme"] if (name == "charts" and stats and stats.available) else [], today),
                page_description=described(f"/{name}/", section_description) if section_description else None,
                **common
            )
            target = dist / name / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(html, encoding="utf-8")
            report.pages += 1

    # Content pages
    for page in pages:
        template_name = {
            "home": "home.html", "page": "page.html", "guide": "guide.html", "chart": "chart.html",
            "basket": "basket.html", "comparisons": "comparisons.html", "converter": "converter.html",
            "network": "network.html", "history": "history.html", "campaign": "campaign.html",
            "route": "route.html",
        }.get(page.template)
        if template_name is None:
            report.error(f"{page.source}: unknown template {page.template!r}")
            continue
        placements = []
        for placement in page.meta.get("placements") or []:
            slug = str(placement.get("slug", "")).strip()
            target = redirects.get(slug)
            if target is None or not target.approved:
                continue  # never render a box for a program that is not approved
            placements.append({**placement, "program": target.program, "url": f"/go/{slug}"})
        codes = []
        for code in page.meta.get("attribution") or []:
            if str(code) not in ATTRIBUTION_LINES:
                report.error(f"{page.source}: unknown attribution code {code!r}; use one of {sorted(ATTRIBUTION_LINES)}")
                continue
            codes.append(str(code))
        attribution = credit_lines(codes, today)
        listed = []
        if page.url != "/" and page.url == f"/{page.section}/":
            listed = sorted(
                (p for p in section_pages.get(page.section, []) if p.url != page.url),
                key=lambda p: (p.meta.get("order", 999), p.title),
            )
        page.body_html = expand_live(page.body_html, stats, report, page)
        if PROGRAMS_TOKEN in page.body_html:
            page.body_html = page.body_html.replace(PROGRAMS_TOKEN, programs_sentence(redirects, today))
        if "[[embed:" in page.body_html:
            page.body_html = expand_embeds(page.body_html, page)
        if re.search(r"\[+\s*art\w*\s*:", page.body_html, flags=re.I):      # a picture token, or something that set out to be one
            page.body_html = expand_art(page.body_html, page)
        for problem in page.quote_problems:
            report.note(f"{page.source}: {problem}")
        # A home page's question cards may quote the explainers: a quoted line is pulled from the passage its page
        # marks (`quoted`), so the card holds no copy that could fall out of step
        for field_name in ("questions", "stories", "tasks", "stops"):
            entries = page.meta.get(field_name)
            if entries is not None and not (isinstance(entries, list) and all(isinstance(entry, dict) for entry in entries)):
                report.error(f"{page.source}: front matter `{field_name}` must be a list of entries, each with its own fields (see the top of lib/content.py)")
                page.meta[field_name] = [entry for entry in entries if isinstance(entry, dict)] if isinstance(entries, list) else []
        for number, card in enumerate(page.meta.get("questions") or [], start=1):
            lines = {}
            for part in ("answer", "example", "missed"):
                value = card.get(part)
                if isinstance(value, dict):
                    lines[part] = quoted(page, value, f"question {number} ({part})")
                elif value:
                    lines[part] = inline(page, value)
            card["lines"] = {part: words for part, words in lines.items() if words}
            if card.get("more") and str(card["more"]) not in by_url:
                report.error(f"{page.source}: question {number} offers the full explanation at {card['more']!r}, which is not a page of this site")
        for name in [page.meta.get("art")] + [s.get("art") for s in (page.meta.get("stories") or [])] + [(page.meta.get("hero") or {}).get("art")]:
            if name:
                art_ready(art, name, page, report)
        # A guided route's knowledge check: the right answer must be one of the options, and each "why" is pulled
        # from a passage marked on the page its stop quotes, so the check says only what the explainer says
        quiz = page.meta.get("check") if isinstance(page.meta.get("check"), dict) else None
        if quiz:
            stops = page.meta.get("stops") or []
            items = quiz.get("questions")
            if not (isinstance(items, list) and all(isinstance(item, dict) for item in items)):
                report.error(f"{page.source}: front matter `check.questions` must be a list of questions, each with q, options, answer, and why")
                items = quiz["questions"] = [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []
            for number, item in enumerate(items, start=1):
                options = item.get("options") if isinstance(item.get("options"), list) else []
                if not isinstance(item.get("answer"), int) or isinstance(item.get("answer"), bool) or not 1 <= item["answer"] <= len(options):
                    report.error(f"{page.source}: check question {number} needs `answer` to be the number of one of its {len(options)} options (a plain number, no quotes)")
                    item["answer"] = 1 if options else 0          # so the page still renders and this line is the error that is seen
                why = item.get("why")
                if isinstance(why, dict):
                    stop = stops[number - 1] if number <= len(stops) else {}
                    shown = None
                    if stop.get("from") in by_url and not why.get("from"):
                        take = stop.get("take") if isinstance(stop.get("take"), int) and not isinstance(stop.get("take"), bool) else None
                        shown = excerpt_markdown(by_url[stop["from"]], under=stop.get("under"), take=take)
                    item["why_html"] = quoted(page, why, f"check question {number} (why)", default_from=stop.get("from"), within=shown) or Markup("")
                else:
                    item["why_html"] = inline(page, why) if why else Markup("")
        # The Stats home page's chart of the week takes turns through a list of charts; a slug that names no chart
        # would silently drop out of the turn, so it is reported.
        if stats and stats.available:
            for entry in ((page.meta.get("weekly") or {}).get("charts") or []) if isinstance(page.meta.get("weekly"), dict) else []:
                if not isinstance(entry, dict) or str(entry.get("slug", "")) not in stats.chart_by_slug:
                    report.error(f"{page.source}: weekly chart {entry!r} names no chart in charts/index.json")
            for story in page.meta.get("stories") or []:
                url = str(story.get("url", ""))
                if url.startswith("/charts/") and url.strip("/").split("/")[-1] not in stats.chart_by_slug:
                    report.error(f"{page.source}: the story {story.get('headline')!r} opens {url}, which is not a chart in charts/index.json")
        hook = page.meta.get("hook_chart") if page.template == "campaign" else None
        if hook:
            # A campaign page shows one Stats chart as its hook. The image files travel with this site's build
            # (every site rebuilds after the Daily Build commits charts/), so the preview works before the domains do.
            slug = str(hook.get("slug", "")).strip()
            copied = 0
            for name in (f"{slug}.png", f"{slug}-dark.png"):
                source = ROOT / "charts" / name
                if source.exists():
                    (dist / "charts").mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dist / "charts" / name)
                    copied += 1
            if copied < 2:
                report.warn(f"{page.source}: hook_chart {slug!r} has no image in charts/ yet (the Daily Build draws it); the page shows a broken image until then")
        try:
            html = env.get_template(template_name).render(
                page=page,
                title=page.title,
                section=page.section,
                section_label=sections.get(page.section, ""),
                placements=placements,
                attribution=attribution,
                sources=page.meta.get("sources") or [],
                understand_first=page.meta.get("understand_first"),
                chart=page.meta.get("chart"),
                listed=listed,
                canonical=site["url"].rstrip("/") + page.url,
                excerpt=lambda spec, page=page: excerpt(page, spec),
                inline=lambda text, page=page: inline(page, text),
                **common,
            )
        except UndefinedError as err:
            # the template asked for a word the front matter (or the data) does not have
            report.error(f"{page.source}: the {template_name} template could not be filled in: {err.message}. Check the page's front matter against the list at the top of lib/content.py")
            continue
        except (TypeError, AttributeError, KeyError, IndexError, ValueError) as err:
            # a front matter value of the wrong kind (a number in quotes, a word where a list belongs)
            report.error(f"{page.source}: the {template_name} template could not be filled in ({type(err).__name__}: {err}). A front matter value is not the kind the template expects; see the list at the top of lib/content.py")
            continue
        target = dist / page.out_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        report.pages += 1

    # Programmatic pages (Stats only): /sats/<amount>-<currency>/ and /items/<slug>/
    generated: list[tuple[str, str]] = []   # (url, lastmod)
    if key == "stats" and stats.available:
        base = site["url"].rstrip("/")

        amount_pages = stats.amount_pages()
        for entry in amount_pages:
            html = env.get_template("amount.html").render(page=None, title=entry["title"], section="sats", canonical=base + entry["url"], entry=entry,
                                                          page_description=described(entry["url"], entry["description"]),
                                                          attribution=credit_lines(["coingecko", "blockchain"] if entry["yearly"] else ["coingecko"], today), **common)
            target = dist / entry["url"].strip("/") / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(html, encoding="utf-8")
            generated.append((entry["url"], today.isoformat()))
        groups = stats.amount_index()
        names = [group["name"] for group in groups]
        number_words = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
        sats_description = (f"See what common amounts buy in sats across {number_words.get(len(groups), len(groups))} currencies. "
                            "Prices are checked hourly, with January history on US dollar pages.")
        html = env.get_template("sats_index.html").render(page=None, title="Money in sats", section="sats", canonical=base + "/sats/", groups=groups,
                                                          currency_names=(", ".join(names[:-1]) + ", or " + names[-1] if len(names) > 2 else " or ".join(names)),
                                                          page_description=described("/sats/", sats_description),
                                                          attribution=credit_lines(["coingecko"], today), **common)
        (dist / "sats").mkdir(parents=True, exist_ok=True)
        (dist / "sats" / "index.html").write_text(html, encoding="utf-8")
        generated.append(("/sats/", today.isoformat()))
        item_pages = stats.item_pages()
        for entry in item_pages:
            html = env.get_template("item.html").render(page=None, title=entry["title"], section="items", canonical=base + entry["url"], entry=entry,
                                                        page_description=described(entry["url"], entry["description"]),
                                                        attribution=credit_lines(["bls", "blockchain"], today), **common)
            target = dist / entry["url"].strip("/") / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(html, encoding="utf-8")
            generated.append((entry["url"], entry["date"]))
        items_description = (f"See {len(item_pages)} everyday items priced in sats using BLS averages for US cities and monthly bitcoin prices, "
                             "with item histories where available.")
        html = env.get_template("items_index.html").render(page=None, title="Everyday items priced in sats", section="items", canonical=base + "/items/", items=item_pages,
                                                           page_description=described("/items/", items_description),
                                                           attribution=credit_lines(["bls", "blockchain"], today), **common)
        (dist / "items").mkdir(parents=True, exist_ok=True)
        (dist / "items" / "index.html").write_text(html, encoding="utf-8")
        generated.append(("/items/", today.isoformat()))
        report.pages += len(amount_pages) + len(item_pages) + 2

    # 404 page
    not_found_description = str(site.get("not_found_description", "")).strip()
    (dist / "404.html").write_text(
        env.get_template("404.html").render(page=None, title="Page not found", section="", canonical=None,
                                            page_description=described("/404.html", not_found_description) if not_found_description else None, **common),
        encoding="utf-8",
    )

    # /go/<slug>/ for a program with no link to follow: a small page that says so. Approved and closed programs
    # redirect instead (lib/redirects.py); Cloudflare follows a redirect even when a file exists, so each slug gets one.
    for slug in sorted(redirects):
        target = redirects[slug]
        if target.forwards:
            continue
        heading = "This link is not live yet" if target.expected else "This link is not live"
        html = env.get_template("go_pending.html").render(page=None, title=heading, section="", canonical=None, entry=target, noindex=True, **common)
        out = dist / "go" / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        report.go_pages += 1

    # Static files: shared first, then the site's own (which may override)
    held_back = {f"{name}-{width}.webp" for name, entry in art.items() if entry.get("status") != "approved" for width in ART_WIDTHS}
    held_back |= {f"{name}-{ART_FALLBACK}.jpg" for name, entry in art.items() if entry.get("status") != "approved"}
    copy_tree(ROOT / "shared" / "static", dist / "static", skip_names=held_back)      # a prepared picture waits for its approval
    copy_tree(site_dir / "static", dist)

    # Data and charts are published by the Stats site only
    if site.get("serves_data"):
        copy_tree(ROOT / "data", dist / "data", skip_names={"README.md", *WITHDRAWN_DATA})   # a withdrawn file is never published
        copy_tree(ROOT / "charts", dist / "charts", skip_names={"README.md"})

    # Cloudflare files
    (dist / "_redirects").write_text(render_redirects_file(redirects), encoding="utf-8")
    (dist / "_headers").write_text((ROOT / "shared" / "_headers").read_text(encoding="utf-8"), encoding="utf-8")
    (dist / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /go/\n\nSitemap: {site['url']}/sitemap.xml\n", encoding="utf-8")

    # Sitemap (content pages and section indexes; never /go/)
    urls = sorted({page.url for page in pages} | {f"/{name}/" for name in sections if section_pages.get(name)})
    entries = []
    for url in urls:
        page = seen.get(url)
        lastmod = (page.updated if page and page.updated else today).isoformat()
        entries.append(f"  <url><loc>{site['url']}{url}</loc><lastmod>{lastmod}</lastmod></url>")
    for url, lastmod in generated:
        entries.append(f"  <url><loc>{site['url']}{url}</loc><lastmod>{lastmod}</lastmod></url>")
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(entries) + "\n</urlset>\n"
    (dist / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    # RSS feed: guides and chart pages with an updated date, newest first
    dated = sorted((p for p in pages if p.updated and not p.shared and p.url != "/" and p.url != f"/{p.section}/"), key=lambda p: p.updated, reverse=True)[:30]
    items = []
    for page in dated:
        link = site["url"].rstrip("/") + page.url
        summary = str(page.meta.get("description", "")).strip()
        pub = _dt.datetime.combine(page.updated, _dt.time(9, 0), tzinfo=_dt.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
        items.append(
            "  <item>\n"
            f"    <title>{_xml(page.title)}</title>\n"
            f"    <link>{link}</link>\n"
            f"    <guid>{link}</guid>\n"
            f"    <pubDate>{pub}</pubDate>\n"
            f"    <description>{_xml(summary)}</description>\n"
            "  </item>"
        )
    feed = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n<channel>\n'
        f"  <title>{_xml(site['name'])}</title>\n  <link>{site['url']}/</link>\n  <description>{_xml(site['description'])}</description>\n"
        f"  <language>en-us</language>\n  <atom:link href=\"{site['url']}/feed.xml\" rel=\"self\" type=\"application/rss+xml\"/>\n"
        + ("\n".join(items) + "\n" if items else "")
        + "</channel>\n</rss>\n"
    )
    (dist / "feed.xml").write_text(feed, encoding="utf-8")

    # A small manifest the agents and the Analyst can read
    manifest = {
        "site": key,
        "built": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "pages": urls,
        "go_slugs": sorted(redirects),
    }
    (dist / "build.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    if strict and report.warnings:
        report.errors.extend(f"(strict) {w}" for w in report.warnings)
    # The last word on the em dash rule: every built page is read once more, so a dash that came in through a
    # template or a sentence put together in lib/ is caught too, not only one typed in a Markdown file.
    for built in sorted(dist.rglob("*.html")):
        if EM_DASH in built.read_text(encoding="utf-8"):
            report.error(f"{built.relative_to(dist)}: the built page contains an em dash; find it in the page, its template, or the words in lib/")

    return report


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    strict = "--strict" in argv
    if not args:
        print(__doc__)
        return 2
    keys = list(SITE_KEYS) if args[0] == "all" else [args[0]]
    out_dir = Path(args[1]) if len(args) > 1 else None
    failed = False
    for key in keys:
        report = build_site(key, out_dir=out_dir if len(keys) == 1 else None, strict=strict)
        print(f"[{key}] {report.pages} pages -> {out_dir or ROOT / 'sites' / key / 'dist'}")
        if report.go_pages:
            print(f"[{key}] {report.go_pages} /go/ links are not live; each shows the \"not live\" page")
        for note in report.notes:
            print(f"[{key}] note: {note}")
            if os.environ.get("GITHUB_ACTIONS") == "true":       # a yellow line on the run's page; the run still passes
                print(f"::warning title=Build note ({key})::{note}")
        for warning in report.warnings:
            print(f"[{key}] warning: {warning}")
        for error in report.errors:
            print(f"[{key}] ERROR: {error}")
        failed = failed or bool(report.errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
