"""Build one site: content/<site>/*.md + shared templates -> sites/<site>/dist/

Run from the repository root:  python3 build.py stats     (or facts, acts, all)
Cloudflare Pages runs the same command for each project; see README.md, "Cloudflare Pages settings".
"""

from __future__ import annotations

import re

import datetime as _dt
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from .content import Page, load_pages
from .redirects import load_redirects, render_redirects_file
from .stats_data import StatsData

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


@dataclass
class Report:
    site: str
    pages: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)


def _xml(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def long_date(value) -> str:
    """October 1, 2026 (portable; strftime's %-d is not available everywhere)."""
    return f"{value:%B} {value.day}, {value.year}" if value else ""


def jinja_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(ROOT / "shared" / "templates")),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["date"] = long_date
    env.filters["isodate"] = lambda value: value.isoformat() if value else ""
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
    items (how many everyday items the basket holds), sp500, sp500-usd, sp500-sats (the S&P 500 row of the comparisons
    table: the index level, the same number as dollars, and that number in sats; baked, not live)."""
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
        if key in ("sp500", "sp500-usd", "sp500-sats"):
            row = stats.sp500_row() if ok else None
            if not row:
                return missing(key)
            return {"sp500": row["level_text"], "sp500-usd": row["dollars_text"], "sp500-sats": row["value_text"]}[key]
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
        if key == "acts" and page.template == "guide" and not page.meta.get("understand_first"):
            report.warn(f"{page.source}: an Acts guide opens with an \"Understand first\" line; add understand_first to the front matter")
        if "\u2014" in page.body_md or "\u2014" in page.title:
            report.error(f"{page.source}: contains an em dash; use a comma, colon, semicolon, or period")

    # Navigation: sections that have at least one page, in site.yml order
    sections = site.get("sections") or {}
    section_pages: dict[str, list[Page]] = {name: [] for name in sections}
    for page in pages:
        if page.section:
            section_pages[page.section].append(page)
    nav = [{"label": label, "url": f"/{name}/"} for name, label in sections.items() if section_pages.get(name)]
    nav += [{"label": page.nav_label, "url": page.url} for page in pages if page.in_nav and not page.section and page.url != "/"]

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

    env = jinja_env()
    common = {
        "site": site,
        "sites": sites,
        "sister_sites": [entry for entry in sites if entry["key"] != key],
        "nav": nav,
        "stats": stats,
        "sats_line": SATS_LINE,
        "disclosure_line": DISCLOSURE_LINE,
        "build_date": today,
        "year": today.year,
    }

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
        html = env.get_template(template_name).render(
            page=page,
            title=page.title,
            section=page.section,
            section_label=sections.get(page.section, ""),
            placements=placements,
            has_affiliate_links=bool(placements or page.go_slugs),
            attribution=attribution,
            sources=page.meta.get("sources") or [],
            understand_first=page.meta.get("understand_first"),
            chart=page.meta.get("chart"),
            listed=listed,
            canonical=site["url"].rstrip("/") + page.url,
            **common,
        )
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

    # Static files: shared first, then the site's own (which may override)
    copy_tree(ROOT / "shared" / "static", dist / "static")
    copy_tree(site_dir / "static", dist)

    # Data and charts are published by the Stats site only
    if site.get("serves_data"):
        copy_tree(ROOT / "data", dist / "data", skip_names={"README.md"})
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
    dated = sorted((p for p in pages if p.updated and p.url != "/" and p.url != f"/{p.section}/"), key=lambda p: p.updated, reverse=True)[:30]
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
        for warning in report.warnings:
            print(f"[{key}] warning: {warning}")
        for error in report.errors:
            print(f"[{key}] ERROR: {error}")
        failed = failed or bool(report.errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
