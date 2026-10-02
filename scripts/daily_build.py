#!/usr/bin/env python3
"""The Daily Build. Runs every morning at 09:00 UTC from .github/workflows/daily-build.yml.

    python3 scripts/daily_build.py              the real thing (needs BLS_KEY and FRED_KEY in the environment)
    python3 scripts/daily_build.py --fixtures   offline run from scripts/fixtures/, for tests
    python3 scripts/daily_build.py --only sats-per-dollar,fear-greed

What it does, in order:
  1. Pull the sources: blockchain.com (price and hash rate since 2009), alternative.me (Fear & Greed),
     BLS (CPI and average prices), FRED (new-home price), the World Bank Pink Sheet (gold),
     and the site's own live API (today's price in 30 currencies, fees, block height).
  2. Write data/*.json. A source that fails keeps yesterday's file and is listed in the summary.
  3. Draw every chart in scripts/chartbook.py (light PNG, dark PNG, SVG) into charts/.
  4. Refresh the chart pages under content/stats/charts/ (the auto block only).
  5. Write charts/index.json and data/latest.json, and print a summary the workflow log shows.
Exit code 1 only when nothing could be built at all; a partial day is still a good day.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import chartbook, pages, series as S  # noqa: E402
from scripts.sources import alternative_me, blockchain_com, bls, fred, live_api, worldbank  # noqa: E402
from scripts.sources.http import SourceError  # noqa: E402
from lib.stats_data import WITHDRAWN_DATA  # noqa: E402

DATA_DIR = ROOT / "data"
CHARTS_DIR = ROOT / "charts"


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def pulled_text(when: dt.datetime) -> str:
    return f"{when:%B} {when.day}, {when.year}, {when:%H:%M} UTC"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def series_file(name: str, title: str, unit: str, frequency: str, source: dict, points: S.Series, when: dt.datetime, extra: dict | None = None, digits: int = 2, significant: int | None = None) -> None:
    payload = {
        "updated": when.isoformat(),
        "source": source,
        "series": {"name": title, "unit": unit, "frequency": frequency, "points": S.to_json(points, digits, significant)},
    }
    if extra:
        payload.update(extra)
    write_json(DATA_DIR / f"{name}.json", payload)


def load_series(name: str) -> S.Series | None:
    """Yesterday's file, used when a source is down today."""
    payload = read_json(DATA_DIR / f"{name}.json")
    try:
        return S.from_json(payload["series"]["points"]) if payload else None
    except (KeyError, TypeError, ValueError):
        return None


def collect_offline(log: list[str]) -> dict:
    """The series the charts need, read from the data/ files written by an earlier run (no network)."""
    saved = read_json(DATA_DIR / "fear-greed.json")
    data = {
        "price_daily": load_series("price-daily"),
        "hashrate_daily": load_series("network"),
        "fear_greed": [(str(d), int(v), str(label)) for d, v, label in saved["series"]["points"]] if saved else None,
        "bls": {name: load_series(name) for name in bls.SERIES if load_series(name)},
        "fred": {"home_price": load_series("homes")},
        "gold_monthly": load_series("gold"),
        "live_price": None,
        "live_fees": None,
    }
    log.append("ok    offline: series read from data/")
    return data


def collect(when: dt.datetime, log: list[str]) -> dict:
    """Pull every source; write its data file; return the series the charts need."""
    data: dict = {}

    def step(label, fn):
        try:
            result = fn()
            log.append(f"ok    {label}")
            return result
        except SourceError as err:
            log.append(f"FAIL  {label}: {err}")
        except Exception as err:  # noqa: BLE001
            log.append(f"FAIL  {label}: {type(err).__name__}: {err}")
            traceback.print_exc()
        return None

    # blockchain.com: price and hash rate, daily since 2009
    price = step("blockchain.com market-price", lambda: blockchain_com.chart("market-price"))
    if price:
        series_file("price-daily", "Bitcoin market price, daily average", "USD", "daily", blockchain_com.SOURCE, price, when)
    data["price_daily"] = price or load_series("price-daily")

    hashrate = step("blockchain.com hash-rate", lambda: blockchain_com.chart("hash-rate"))
    if hashrate:
        # nine significant figures: whole terahashes today, and the fractions of a terahash of 2009 to early 2011 kept
        # (rounded to whole numbers, those first two years were saved as zero)
        series_file("network", "Estimated hash rate", "TH/s", "daily", blockchain_com.SOURCE, hashrate, when, significant=9)
    data["hashrate_daily"] = hashrate or load_series("network")

    # alternative.me
    fng = step("alternative.me fear and greed", alternative_me.history)
    if fng:
        write_json(DATA_DIR / "fear-greed.json", {
            "updated": when.isoformat(), "source": alternative_me.SOURCE,
            "series": {"name": "Crypto Fear & Greed Index", "unit": "index 0-100", "frequency": "daily",
                       "points": [[d, v, label] for d, v, label in fng]},
        })
        data["fear_greed"] = fng
    else:
        saved = read_json(DATA_DIR / "fear-greed.json")
        data["fear_greed"] = [(str(d), int(v), str(label)) for d, v, label in saved["series"]["points"]] if saved else None

    # BLS
    bls_series = step("BLS monthly series", bls.monthly)
    if bls_series:
        for name, points in bls_series.items():
            spec = bls.SERIES[name]
            series_file(name if name != "cpi" else "cpi", spec["title"], spec["unit"], "monthly", bls.SOURCE, points, when,
                        extra={"bls_series_id": spec["id"]}, digits=3)
        # A BLS file whose item has left the table (lib/stats_data.py ITEMS) is removed, so data/ holds only what is defined
        for path in sorted(DATA_DIR.glob("*.json")):
            if path.stem not in bls.SERIES and "bls_series_id" in (read_json(path) or {}):
                path.unlink()
                log.append(f"ok    removed data/{path.name}: its series is no longer in the item table")
        data["bls"] = bls_series
    else:
        data["bls"] = {name: load_series(name) for name in bls.SERIES if load_series(name)}

    # FRED
    fred_series = step("FRED series", fred.all_series)
    if fred_series:
        for name, points in fred_series.items():
            spec = fred.SERIES[name]
            series_file("homes" if name == "home_price" else name, spec["title"], spec["unit"], spec["frequency"], fred.SOURCE, points, when,
                        extra={"fred_series_id": spec["id"]})
        data["fred"] = fred_series
    else:
        data["fred"] = {"home_price": load_series("homes")}

    # A file that has been withdrawn from the site (lib/stats_data.py WITHDRAWN_DATA) is deleted, whether or not its
    # source answered today, so the repository stops carrying it too
    for name in WITHDRAWN_DATA:
        path = DATA_DIR / name
        if path.exists():
            path.unlink()
            log.append(f"ok    removed data/{name}: withdrawn from the site")

    # World Bank gold
    gold = step("World Bank Pink Sheet gold", worldbank.gold_monthly)
    if gold:
        series_file("gold", "Gold, USD per troy ounce, monthly average", "USD per troy ounce", "monthly", worldbank.SOURCE, gold, when)
    data["gold_monthly"] = gold or load_series("gold")

    # The site's live API
    data["live_price"] = step("live API /price", live_api.price)
    data["live_fees"] = step("live API /fees", live_api.fees)
    return data


def write_latest(data: dict, entries: list[dict], when: dt.datetime) -> None:
    """data/latest.json: the headline figures the pages and agents read."""
    by_slug = {e["slug"]: e for e in entries}
    live = data.get("live_price") or {}
    fees = data.get("live_fees") or {}
    price_daily = data.get("price_daily") or []
    latest = {
        "updated": when.isoformat(),
        "price": {
            "usd": (live.get("prices") or {}).get("usd"),
            "prices": live.get("prices"),
            "sats_per": live.get("sats_per"),
            "change_24h": live.get("change_24h"),
            "updated": live.get("updated"),
            "source": live.get("source") or {"name": "CoinGecko", "url": "https://www.coingecko.com"},
        },
        "price_daily_average": {"date": price_daily[-1][0], "usd": round(price_daily[-1][1], 2), "source": blockchain_com.SOURCE} if price_daily else None,
        "sats_per_dollar": (live.get("sats_per") or {}).get("usd") or (round(100_000_000 / price_daily[-1][1]) if price_daily else None),
        "fees": {"fast": (fees.get("fees") or {}).get("fast"), "medium": (fees.get("fees") or {}).get("medium"), "slow": (fees.get("fees") or {}).get("slow"),
                 "unit": "sat/vB", "height": fees.get("height"), "updated": fees.get("updated"), "source": fees.get("source") or {"name": "mempool.space", "url": "https://mempool.space"}},
        "charts": {slug: {"date": e["latest"]["date"], "value": e["latest"]["value"], "text": e["latest"]["text"], "finding": e["title"]} for slug, e in by_slug.items()},
    }
    fng = data.get("fear_greed")
    if fng:
        latest["fear_greed"] = {"value": fng[-1][1], "label": fng[-1][2], "date": fng[-1][0], "source": alternative_me.SOURCE}
    cpi = (data.get("bls") or {}).get("cpi")
    if cpi:
        latest["cpi"] = {"value": cpi[-1][1], "period": cpi[-1][0][:7], "series": bls.SERIES["cpi"]["id"], "source": bls.SOURCE}
    write_json(DATA_DIR / "latest.json", latest)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="The Daily Build")
    parser.add_argument("--fixtures", action="store_true", help="read scripts/fixtures/ instead of the network")
    parser.add_argument("--only", default="", help="comma-separated chart slugs to draw (default: all)")
    parser.add_argument("--skip-pages", action="store_true", help="do not touch content/stats/charts/")
    parser.add_argument("--offline", action="store_true", help="redraw the charts from the saved data/ files without touching any source (data/latest.json is left alone)")
    args = parser.parse_args(argv)
    if args.fixtures:
        os.environ["SATS_FIXTURES"] = "1"

    when = now_utc()
    today = when.date()
    log: list[str] = []
    if args.offline:
        data = collect_offline(log)
        saved = read_json(DATA_DIR / "price-daily.json") or {}
        try:
            when = dt.datetime.fromisoformat(saved["updated"])
        except (KeyError, TypeError, ValueError):
            pass
        today = when.date()
    else:
        data = collect(when, log)

    wanted = {s.strip() for s in args.only.split(",") if s.strip()}
    entries: list[dict] = []
    pulled = pulled_text(when)
    for build in chartbook.BUILDERS:
        if wanted and build.__name__.replace("_", "-") not in wanted:
            continue
        try:
            entry = build(data, CHARTS_DIR, pulled)
        except Exception as err:  # noqa: BLE001
            log.append(f"FAIL  chart {build.__name__}: {type(err).__name__}: {err}")
            traceback.print_exc()
            continue
        if entry is None:
            log.append(f"skip  chart {build.__name__}: data missing")
            continue
        entry["drawn_at"] = when.isoformat()
        entry["page"] = f"/charts/{entry['slug']}/"
        entry["png"] = f"/charts/{entry['slug']}.png"
        entry["png_dark"] = f"/charts/{entry['slug']}-dark.png"
        entry["svg"] = f"/charts/{entry['slug']}.svg"
        entries.append(entry)
        log.append(f"ok    chart {entry['slug']}: {entry['title']}")
        if not args.skip_pages:
            pages.write_page(entry, pulled, today)

    # Keep index entries for charts that were skipped today (their last image still exists)
    previous = read_json(CHARTS_DIR / "index.json") or {}
    kept = {e["slug"]: e for e in previous.get("charts") or [] if isinstance(e, dict) and "slug" in e}
    for entry in entries:
        kept[entry["slug"]] = entry
    ordered = [kept[s] for s in [b.__name__.replace("_", "-") for b in chartbook.BUILDERS] if s in kept]
    ordered += [e for s, e in kept.items() if e not in ordered]
    index = {"updated": when.isoformat(), "site": chartbook.STATS_URL, "charts": ordered}
    write_json(CHARTS_DIR / "index.json", index)
    if not args.offline:
        write_latest(data, ordered, when)

    print("Daily Build", when.isoformat())
    for line in log:
        print("  " + line)
    failures = sum(1 for line in log if line.startswith("FAIL"))
    print(f"  charts drawn: {len(entries)}, sources failed: {failures}")
    return 0 if entries else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
