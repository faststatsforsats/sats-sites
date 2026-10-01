"""Build one site: content/<site>/*.md + shared templates -> sites/<site>/dist/

Run from the repository root:  python3 build.py stats     (or facts, acts, all)
Cloudflare Pages runs the same command for each project; see README.md, "Cloudflare Pages settings".
"""

from __future__ import annotations

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

ROOT = Path(__file__).resolve().parent.parent
SITE_KEYS = ("stats", "facts", "acts")

ATTRIBUTION_LINES = {
    "coingecko": {"text": "Data provided by CoinGecko", "url": "https://www.coingecko.com"},
    "fred": {"text": "This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis.", "url": "https://fred.stlouisfed.org"},
    "bls": {"text": "Source: U.S. Bureau of Labor Statistics, retrieved {date}. BLS.gov cannot vouch for the data or analyses derived from these data after the data have been retrieved from BLS.gov.", "url": "https://www.bls.gov"},
    "altme": {"text": "Source: alternative.me", "url": "https://alternative.me/crypto/fear-and-greed-index/"},
    "mempool": {"text": "Fee data: mempool.space", "url": "https://mempool.space"},
    "blockchain": {"text": "Price and network data: blockchain.com", "url": "https://www.blockchain.com/explorer/charts"},
    "worldbank": {"text": "Gold price: World Bank Commodity Price Data (The Pink Sheet), CC BY 4.0", "url": "https://www.worldbank.org/en/research/commodity-markets"},
}

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
        if key == "acts" and page.template == "guide" and not page.meta.get("understand_first"):
            report.warn(f"{page.source}: an Acts guide opens with an \"Understand first\" line; add understand_first to the front matter")
        if "—" in page.body_md or "—" in page.title:
            report.error(f"{page.source}: contains an em dash; use a comma, colon, semicolon, or period")

    # Navigation: sections that have at least one page, in site.yml order
    sections = site.get("sections") or {}
    section_pages: dict[str, list[Page]] = {name: [] for name in sections}
    for page in pages:
        if page.section:
            section_pages[page.section].append(page)
    nav = [{"label": label, "url": f"/{name}/"} for name, label in sections.items() if section_pages.get(name)]
    nav += [{"label": page.title, "url": page.url} for page in pages if page.in_nav and not page.section and page.url != "/"]

    env = jinja_env()
    common = {
        "site": site,
        "sites": sites,
        "sister_sites": [entry for entry in sites if entry["key"] != key],
        "nav": nav,
        "sats_line": SATS_LINE,
        "disclosure_line": DISCLOSURE_LINE,
        "build_date": today,
        "year": today.year,
    }

    # Section index pages that have no index.md of their own
    for name, label in sections.items():
        listed = sorted(section_pages.get(name, []), key=lambda p: (p.meta.get("order", 999), p.title))
        if listed and f"/{name}/" not in seen:
            html = env.get_template("section.html").render(
                page=None, title=label, section=name, canonical=site["url"].rstrip("/") + f"/{name}/",
                listed=[p for p in listed if p.url != f"/{name}/"], **common
            )
            target = dist / name / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(html, encoding="utf-8")
            report.pages += 1

    # Content pages
    for page in pages:
        template_name = {"home": "home.html", "page": "page.html", "guide": "guide.html", "chart": "chart.html"}.get(page.template)
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
        attribution = []
        for code in page.meta.get("attribution") or []:
            line = ATTRIBUTION_LINES.get(str(code))
            if line is None:
                report.error(f"{page.source}: unknown attribution code {code!r}; use one of {sorted(ATTRIBUTION_LINES)}")
                continue
            attribution.append({"text": line["text"].format(date=long_date(today)), "url": line["url"]})
        listed = []
        if page.url != "/" and page.url == f"/{page.section}/":
            listed = sorted(
                (p for p in section_pages.get(page.section, []) if p.url != page.url),
                key=lambda p: (p.meta.get("order", 999), p.title),
            )
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

    # 404 page
    (dist / "404.html").write_text(
        env.get_template("404.html").render(page=None, title="Page not found", section="", canonical=None, **common),
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
