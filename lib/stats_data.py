"""Everything the Stats site shows that comes from data/ and charts/ rather than from a Markdown file.

Read once per build by lib/site.py (Stats only) and handed to the templates as `stats`. Standard library only,
so the Cloudflare build needs nothing beyond requirements.txt. When data/ holds only the placeholders (before
the first Daily Build), `available` is False and the templates fall back to plain text.

Also produces the programmatic pages: /sats/<amount>-<currency>/ (how many sats an amount buys) and
/items/<slug>/ (an everyday item priced in sats), which site.py renders from these dicts.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from bisect import bisect_right
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CHARTS = ROOT / "charts"

START_YEAR = 2011

# Data files that are no longer published. The Stats build leaves them out of the site even while a copy is still in
# data/, and the Daily Build deletes that copy on its next run (scripts/daily_build.py).
# sp500.json: the S&P 500 series belongs to S&P Dow Jones Indices, and FRED's page for it says it may not be
# reproduced without S&P's written permission. The comparisons page's S&P 500 row and this file came off the site on
# October 2, 2026, at Jim's call, until S&P answers. To bring them back: take the name out of this list, put the
# series back in scripts/sources/fred.py, and restore the row and Jim's wording (claude/stats-review-baseline.md).
WITHDRAWN_DATA = ("sp500.json",)

# 54 amounts x 5 currencies = 270 "in sats" pages
AMOUNTS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 100, 120, 125, 150, 175, 200,
           250, 300, 350, 400, 450, 500, 600, 700, 750, 800, 900, 1000, 1200, 1500, 2000, 2500, 3000, 4000, 5000, 7500,
           10000, 15000, 20000, 25000, 50000, 100000]
CURRENCIES = {
    "usd": {"symbol": "$", "name": "US dollars", "one": "a dollar", "adjective": "US dollar"},
    "eur": {"symbol": "€", "name": "euros", "one": "a euro", "adjective": "euro"},
    "gbp": {"symbol": "£", "name": "British pounds", "one": "a pound", "adjective": "pound"},
    "cad": {"symbol": "C$", "name": "Canadian dollars", "one": "a Canadian dollar", "adjective": "Canadian dollar"},
    "aud": {"symbol": "A$", "name": "Australian dollars", "one": "an Australian dollar", "adjective": "Australian dollar"},
}

# Everyday items, one table for both halves of the system: the BLS series the Daily Build asks for (id, BLS's item
# name, the unit written into the data file) and how the pages talk about the item. scripts/sources/bls.py builds its
# request from this table, and the site shows only the items listed here whose data file was written for the id given
# here, so an item cannot be labeled in one place and defined in another.
# Every id was checked against BLS's own item list, https://download.bls.gov/pub/time.series/ap/ap.item, on
# October 2, 2026. Check a new item there before adding it: the series id is "APU0000" plus the item code
# (fuel and utility items have five-digit codes, so gasoline is "APU0000" + "74714").
# Retired: apples (APU0000711111, Red Delicious), which BLS stopped publishing after October 2017.
ITEMS = {
    "eggs": {"id": "APU0000708111", "group": "food", "title": "Eggs, grade A, large, per dozen, U.S. city average", "data_unit": "USD per dozen",
             "name": "A dozen eggs", "short": "a dozen large eggs", "unit": "per dozen", "chart": "eggs-in-sats"},
    "gasoline": {"id": "APU000074714", "group": "transport", "title": "Gasoline, unleaded regular, per gallon, U.S. city average", "data_unit": "USD per gallon",
                 "name": "A gallon of gas", "short": "a gallon of regular gasoline", "unit": "per gallon"},
    "milk": {"id": "APU0000709112", "group": "food", "title": "Milk, fresh, whole, fortified, per gallon, U.S. city average", "data_unit": "USD per gallon",
             "name": "A gallon of milk", "short": "a gallon of whole milk", "unit": "per gallon"},
    "bread": {"id": "APU0000702111", "group": "food", "title": "Bread, white, pan, per pound, U.S. city average", "data_unit": "USD per pound",
              "name": "A pound of white bread", "short": "a pound of white bread", "unit": "per pound"},
    "coffee": {"id": "APU0000717311", "group": "food", "title": "Coffee, 100%, ground roast, all sizes, per pound, U.S. city average", "data_unit": "USD per pound",
               "name": "A pound of coffee", "short": "a pound of ground coffee", "unit": "per pound"},
    "ground_beef": {"id": "APU0000703112", "group": "food", "title": "Ground beef, 100% beef, per pound, U.S. city average", "data_unit": "USD per pound",
                    "name": "A pound of ground beef", "short": "a pound of ground beef", "unit": "per pound"},
    "electricity": {"id": "APU000072610", "group": "home", "title": "Electricity, per kilowatt-hour, U.S. city average", "data_unit": "USD per kWh",
                    "name": "A kilowatt-hour of electricity", "short": "a kilowatt-hour of electricity", "unit": "per kWh"},
    "bananas": {"id": "APU0000711211", "group": "food", "title": "Bananas, per pound, U.S. city average", "data_unit": "USD per pound",
                "name": "A pound of bananas", "short": "a pound of bananas", "unit": "per pound"},
    "chicken": {"id": "APU0000706111", "group": "food", "title": "Chicken, fresh, whole, per pound, U.S. city average", "data_unit": "USD per pound",
                "name": "A pound of chicken", "short": "a pound of fresh whole chicken", "unit": "per pound"},
    "bacon": {"id": "APU0000704111", "group": "food", "title": "Bacon, sliced, per pound, U.S. city average", "data_unit": "USD per pound",
              "name": "A pound of bacon", "short": "a pound of sliced bacon", "unit": "per pound"},
    "flour": {"id": "APU0000701111", "group": "food", "title": "Flour, white, all purpose, per pound, U.S. city average", "data_unit": "USD per pound",
              "name": "A pound of flour", "short": "a pound of all-purpose flour", "unit": "per pound"},
    "rice": {"id": "APU0000701312", "group": "food", "title": "Rice, white, long grain, uncooked, per pound, U.S. city average", "data_unit": "USD per pound",
             "name": "A pound of rice", "short": "a pound of long-grain rice", "unit": "per pound"},
    "sugar": {"id": "APU0000715211", "group": "food", "title": "Sugar, white, all sizes, per pound, U.S. city average", "data_unit": "USD per pound",
              "name": "A pound of sugar", "short": "a pound of white sugar", "unit": "per pound"},
    "butter": {"id": "APU0000FS1101", "group": "food", "title": "Butter, stick, per pound, U.S. city average", "data_unit": "USD per pound",
               "name": "A pound of butter", "short": "a pound of stick butter", "unit": "per pound"},
    "potatoes": {"id": "APU0000712112", "group": "food", "title": "Potatoes, white, per pound, U.S. city average", "data_unit": "USD per pound",
                 "name": "A pound of potatoes", "short": "a pound of white potatoes", "unit": "per pound"},
    "tomatoes": {"id": "APU0000712311", "group": "food", "title": "Tomatoes, field grown, per pound, U.S. city average", "data_unit": "USD per pound",
                 "name": "A pound of tomatoes", "short": "a pound of field-grown tomatoes", "unit": "per pound"},
    "oranges": {"id": "APU0000711311", "group": "food", "title": "Oranges, navel, per pound, U.S. city average", "data_unit": "USD per pound",
                "name": "A pound of oranges", "short": "a pound of navel oranges", "unit": "per pound"},
    "wheat_bread": {"id": "APU0000702212", "group": "food", "title": "Bread, whole wheat, pan, per pound, U.S. city average", "data_unit": "USD per pound",
                    "name": "A pound of whole wheat bread", "short": "a pound of whole wheat bread", "unit": "per pound"},
    "diesel": {"id": "APU000074717", "group": "transport", "title": "Automotive diesel fuel, per gallon, U.S. city average", "data_unit": "USD per gallon",
               "name": "A gallon of diesel", "short": "a gallon of diesel", "unit": "per gallon"},
    "premium_gas": {"id": "APU000074716", "group": "transport", "title": "Gasoline, unleaded premium, per gallon, U.S. city average", "data_unit": "USD per gallon",
                    "name": "A gallon of premium gas", "short": "a gallon of premium gasoline", "unit": "per gallon"},
    "natural_gas": {"id": "APU000072620", "group": "home", "title": "Utility (piped) gas, per therm, U.S. city average", "data_unit": "USD per therm",
                    "name": "A therm of natural gas", "short": "a therm of piped natural gas", "unit": "per therm"},
    "fuel_oil": {"id": "APU000072511", "group": "home", "title": "Fuel oil #2, per gallon, U.S. city average", "data_unit": "USD per gallon",
                 "name": "A gallon of heating oil", "short": "a gallon of No. 2 fuel oil", "unit": "per gallon"},
    "beer": {"id": "APU0000720111", "group": "drinks", "title": "Malt beverages, all types, all sizes, any origin, per 16 ounces, U.S. city average", "data_unit": "USD per 16 oz",
             "name": "A pint of beer", "short": "16 ounces of beer", "unit": "per 16 oz"},
    "wine": {"id": "APU0000720311", "group": "drinks", "title": "Wine, red and white table, all sizes, any origin, per liter, U.S. city average", "data_unit": "USD per liter",
             "name": "A liter of wine", "short": "a liter of table wine", "unit": "per liter"},
}
# An item whose series stopped this many months before the newest item's month is left off the pages,
# so an old price is never shown as this month's.
STALE_AFTER_MONTHS = 6

# How the everyday-prices table is grouped (Jim's plan of October 2026: "feature a smaller mix of food, transport and
# housing" instead of an alphabetical list that opens with several fuels). The group names are drafted for his review.
ITEM_GROUPS = {"food": "Food", "home": "Home and energy", "transport": "Transport", "drinks": "Drinks"}
# The mix the home page features, in this order: four foods, one transport, one home item.
FEATURED_ITEMS = ("eggs", "milk", "bread", "coffee", "gasoline", "electricity")
_ungrouped = sorted(stem for stem, item in ITEMS.items() if item.get("group") not in ITEM_GROUPS)
if _ungrouped:      # caught when the module loads, so an item cannot drop out of the grouped table unnoticed
    raise SystemExit(f"ERROR: lib/stats_data.py: ITEMS {_ungrouped} need a group from ITEM_GROUPS ({', '.join(ITEM_GROUPS)})")

# The words of the home page's first-screen comparison (Jim's plan: "a large comparison with Today / One year / Five
# years controls, one plain takeaway, a clear data date"). The row names come from his introduction ("A dollar. A
# dozen eggs. A place to live."); the sentences are drafted for his review. A change is always named in words
# ("more sats per dollar"), never left to a color or a sign: fewer sats for the same eggs can mean more buying power.
COMPARE_ROWS = {
    "dollar": {"name": "A dollar", "chart": "/charts/sats-per-dollar/", "per": "per dollar", "unit": "sats", "more": "more sats", "fewer": "fewer sats",
               "basis": "daily average"},
    "eggs": {"name": "A dozen eggs", "chart": "/charts/eggs-in-sats/", "per": "per dozen", "unit": "sats", "more": "more sats", "fewer": "fewer sats",
             "basis": "monthly average", "latest": "Latest month"},
    "home": {"name": "A new home", "chart": "/charts/home-in-bitcoin/", "per": "per home", "unit": "bitcoin", "more": "more bitcoin", "fewer": "less bitcoin",
             "basis": "quarterly figure", "latest": "Latest quarter"},
}
# When the source has no figure for the matching earlier period (most BLS average prices skip October 2025), the row says so
COMPARE_MISSING = "The source has no figure for {when}."
COMPARE_SPANS = {"y1": {"years": 1, "label": "One year", "earlier": "a year earlier"}, "y5": {"years": 5, "label": "Five years", "earlier": "five years earlier"}}
TAKEAWAY_TODAY = "A dollar buys {figure} at the latest price."
TAKEAWAY_MORE = "A dollar buys {pct} more sats than {earlier}, because bitcoin's dollar price is lower."
TAKEAWAY_FEWER = "A dollar buys {pct} fewer sats than {earlier}, because bitcoin's dollar price is higher."
TAKEAWAY_SAME = "A dollar buys about as many sats as it did {earlier}."


def _read(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _points(payload) -> list[tuple[str, float]]:
    try:
        return [(str(d), float(v)) for d, v, *_ in payload["series"]["points"]]
    except (KeyError, TypeError, ValueError):
        return []


def _on_or_before(series, day: str):
    days = [d for d, _ in series]
    idx = bisect_right(days, day)
    return series[idx - 1] if idx else None


def _months_between(earlier: str, later: str) -> int:
    return (int(later[:4]) - int(earlier[:4])) * 12 + int(later[5:7]) - int(earlier[5:7])


def _years_ago(series, day: str, years: int = 1):
    """The point on or before the same date that many years earlier."""
    d = dt.date.fromisoformat(day[:10])
    try:
        target = d.replace(year=d.year - years)
    except ValueError:
        target = d.replace(year=d.year - years, day=28)
    return _on_or_before(series, target.isoformat())


def _year_ago(series, day: str):
    return _years_ago(series, day, 1)


def _same_period_a_year_ago(series, day: str):
    """For a monthly or quarterly series: the point for the same month one year earlier, or None when the source has
    none. The nearest earlier month will not do: BLS has no October 2025 figure for 22 of the 24 items here (the two
    gasolines have one), and a table that says "a year ago" must not show September's."""
    point = _year_ago(series, day)
    return point if point and point[0][:7] == f"{int(day[:4]) - 1:04d}{day[4:7]}" else None


def short_date(day: str) -> str:
    """Oct 2, 2026"""
    d = dt.date.fromisoformat(day[:10])
    return f"{d:%b} {d.day}, {d.year}"


def short_month(day: str) -> str:
    """Aug 2026"""
    d = dt.date.fromisoformat(day[:10])
    return f"{d:%b} {d.year}"


def pct_text(change: float) -> str:
    """How big a change is, without its sign: 40%, 5.7%, 118%. Whole numbers from 10% up."""
    size = abs(change)
    if size >= 10:
        return f"{size:.0f}%"
    text = f"{size:.1f}"
    return (text[:-2] if text.endswith(".0") else text) + "%"


def long_date(day: str) -> str:
    d = dt.date.fromisoformat(day[:10])
    return f"{d:%B} {d.day}, {d.year}"


def month_name(day: str) -> str:
    d = dt.date.fromisoformat(day[:10])
    return f"{d:%B} {d.year}"


def quarter(day: str) -> str:
    d = dt.date.fromisoformat(day[:10])
    return f"Q{(d.month - 1) // 3 + 1} {d.year}"


def fmt_sats(value: float) -> str:
    if value >= 100:
        return f"{value:,.0f} sats"
    if value >= 10:
        return f"{value:,.1f} sats"
    return f"{value:,.2f} sats"


def fmt_money(value: float, symbol: str = "$") -> str:
    if value >= 1000:
        return f"{symbol}{value:,.0f}"
    if value >= 1:
        return f"{symbol}{value:,.2f}"
    text = f"{value:,.3f}"
    return symbol + (text[:-1] if text.endswith("0") else text)


def fmt_btc(value: float) -> str:
    if value >= 10:
        return f"{value:,.1f} bitcoin"
    if value >= 1:
        return f"{value:,.2f} bitcoin"
    return f"{value:,.4f} bitcoin"


def slugify(text: str) -> str:
    out = "".join(c.lower() if c.isalnum() else "-" for c in text)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")


class StatsData:
    def __init__(self, root: Path = ROOT):
        self.root = root
        self.latest = _read(root / "data" / "latest.json") or {}
        self.index = _read(root / "charts" / "index.json") or {}
        self.charts = [c for c in self.index.get("charts") or [] if isinstance(c, dict) and c.get("slug")]
        self.chart_by_slug = {c["slug"]: c for c in self.charts}
        self.price_daily = _points(_read(root / "data" / "price-daily.json"))
        self.available = bool(self.price_daily) and bool(self.latest.get("updated"))
        self.updated = self.latest.get("updated")
        self.updated_text = ""
        if self.updated:
            when = dt.datetime.fromisoformat(self.updated.replace("Z", "+00:00"))
            self.updated_text = f"{when:%B} {when.day}, {when.year}, {when:%H:%M} UTC"

        live = self.latest.get("price") or {}
        self.prices = {k: float(v) for k, v in (live.get("prices") or {}).items() if isinstance(v, (int, float))}
        self.change_24h = live.get("change_24h") or {}
        daily = self.latest.get("price_daily_average") or {}
        self.price_usd = self.prices.get("usd") or daily.get("usd") or (self.price_daily[-1][1] if self.price_daily else None)
        self.price_date = daily.get("date") or (self.price_daily[-1][0] if self.price_daily else None)
        self.sats_per_dollar = round(100_000_000 / self.price_usd) if self.price_usd else None
        self.sats_per = {cur: round(100_000_000 / p) for cur, p in self.prices.items() if p}
        if "usd" not in self.sats_per and self.sats_per_dollar:
            self.sats_per["usd"] = self.sats_per_dollar
            if self.price_usd:
                self.prices["usd"] = self.price_usd

        self.fees = self.latest.get("fees") or {}
        self.fees_updated_text = self.updated_text   # the build's own time when the fee feed gave none
        try:
            fee_time = dt.datetime.fromisoformat(str(self.fees.get("updated")).replace("Z", "+00:00")).astimezone(dt.timezone.utc)
            self.fees_updated_text = f"{fee_time:%B} {fee_time.day}, {fee_time.year}, {fee_time:%H:%M} UTC"
        except ValueError:
            pass
        self.fear_greed = self.latest.get("fear_greed")
        self.cpi = self.latest.get("cpi")
        self.network = _points(_read(root / "data" / "network.json"))
        self.gold = _points(_read(root / "data" / "gold.json"))
        self.homes = _points(_read(root / "data" / "homes.json"))
        self.items_data = self._load_items()

        self.monthly_avg = self._monthly_average(self.price_daily)
        self.quarterly_avg = self._quarterly_average(self.price_daily)

    # ------------------------------------------------------------------ loading

    def _load_items(self) -> dict:
        """The everyday items the pages show: listed in ITEMS, with a data file written for the series id given there,
        and current. A file written for another id (the table changed since the last Daily Build) or a series that
        stopped long ago is left out rather than shown under the wrong name or as this month's price."""
        loaded = {}
        for stem, meta in ITEMS.items():
            payload = _read(self.root / "data" / f"{stem}.json")
            points = _points(payload)
            if not points or (payload or {}).get("bls_series_id") != meta["id"]:
                continue
            loaded[stem] = {
                "slug": slugify(stem.replace("_", "-")),
                "stem": stem,
                "name": meta["name"],
                "short": meta["short"],
                "unit": meta["unit"],
                "group": meta.get("group", "food"),
                "chart": meta.get("chart"),
                "series_title": meta["title"],
                "series_id": meta["id"],
                "points": points,
                "data_file": f"/data/{stem}.json",
            }
        if not loaded:
            return loaded
        newest = max(item["points"][-1][0] for item in loaded.values())
        return {stem: item for stem, item in loaded.items() if _months_between(item["points"][-1][0], newest) <= STALE_AFTER_MONTHS}

    @staticmethod
    def _monthly_average(series):
        buckets: dict[str, list[float]] = {}
        for day, value in series:
            buckets.setdefault(day[:7] + "-01", []).append(value)
        return {k: sum(v) / len(v) for k, v in buckets.items()}

    @staticmethod
    def _quarterly_average(series):
        buckets: dict[str, list[float]] = {}
        for day, value in series:
            d = dt.date.fromisoformat(day)
            key = f"{d.year:04d}-{3 * ((d.month - 1) // 3) + 1:02d}-01"
            buckets.setdefault(key, []).append(value)
        return {k: sum(v) / len(v) for k, v in buckets.items()}

    # ------------------------------------------------------------------ derived tables

    def price_on(self, day: str):
        point = _on_or_before(self.price_daily, day)
        return point[1] if point else None

    def january_prices(self) -> list[tuple[int, str, float]]:
        """(year, date, usd) for the first available day of January each year since START_YEAR."""
        out = []
        years = {}
        for day, value in self.price_daily:
            year = int(day[:4])
            if year >= START_YEAR and day[5:7] == "01" and year not in years:
                years[year] = (day, value)
        for year in sorted(years):
            day, value = years[year]
            out.append((year, day, value))
        return out

    def basket(self) -> list[dict]:
        rows = []
        for stem, item in self.items_data.items():
            day, usd = item["points"][-1]
            btc = self.monthly_avg.get(day)
            if not btc:
                continue
            sats = usd / btc * 100_000_000
            ago = _same_period_a_year_ago(item["points"], day)
            sats_ago = None
            if ago and self.monthly_avg.get(ago[0]):
                sats_ago = ago[1] / self.monthly_avg[ago[0]] * 100_000_000
            rows.append({
                **{k: v for k, v in item.items() if k != "points"},
                "month": month_name(day), "date": day, "usd": usd, "usd_text": fmt_money(usd),
                "sats": sats, "sats_text": fmt_sats(sats),
                "sats_ago": sats_ago, "sats_ago_text": fmt_sats(sats_ago) if sats_ago else "",
                "change_pct": (sats / sats_ago - 1) * 100 if sats_ago else None,
                "url": f"/items/{item['slug']}/",
            })
        rows.sort(key=lambda r: r["name"])
        return rows

    def item_pages(self) -> list[dict]:
        pages = []
        for row in self.basket():
            item = self.items_data[row["stem"]]
            yearly = []
            for year, _day, _usd in self.january_prices():
                point = _on_or_before(item["points"], f"{year:04d}-01-31")
                if not point or point[0][:4] != str(year):
                    continue
                btc = self.monthly_avg.get(point[0])
                if btc:
                    yearly.append({"year": year, "usd_text": fmt_money(point[1]), "sats": point[1] / btc * 1e8, "sats_text": fmt_sats(point[1] / btc * 1e8)})
            title = f"{row['name']} in sats"
            pages.append({
                **row,
                "title": title if len(title) <= 60 else title[:57] + "...",
                "heading": f"{row['name']} priced in sats",
                "since": yearly[0]["year"] if yearly else None,
                "description": f"See the sats cost of {row['short']} using the latest BLS average price for US cities"
                               + (f", with January history since {yearly[0]['year']}." if yearly else "."),
                "finding": f"{row['name']} cost the equivalent of {row['sats_text']} in {row['month']}, using the US city average price of {row['usd_text']} {row['unit']}.",
                "yearly": yearly,
                "chart_entry": self.chart_by_slug.get(row["chart"]) if row.get("chart") else None,
            })
        return pages

    def comparisons(self) -> list[dict]:
        rows = []
        if self.gold:
            day, usd = self.gold[-1]
            btc = self.monthly_avg.get(day)
            if btc:
                ago = _same_period_a_year_ago(self.gold, day)
                ago_sats = ago[1] / self.monthly_avg[ago[0]] * 1e8 if ago and self.monthly_avg.get(ago[0]) else None
                rows.append({"name": "A troy ounce of gold", "when": month_name(day), "usd_text": fmt_money(usd), "value_text": fmt_sats(usd / btc * 1e8),
                             "ago_text": fmt_sats(ago_sats) if ago_sats else "", "chart": "gold-in-sats", "source": "World Bank Pink Sheet (gold), blockchain.com (price)", "data_file": "/data/gold.json"})
        if self.homes:
            day, usd = self.homes[-1]
            btc = self.quarterly_avg.get(day)
            if btc:
                ago = _same_period_a_year_ago(self.homes, day)
                ago_btc = ago[1] / self.quarterly_avg[ago[0]] if ago and self.quarterly_avg.get(ago[0]) else None
                rows.append({"name": "US median new-home sale price", "when": quarter(day), "usd_text": fmt_money(usd), "value_text": fmt_btc(usd / btc),
                             "ago_text": fmt_btc(ago_btc) if ago_btc else "", "chart": "home-in-bitcoin", "source": "FRED (MSPUS), blockchain.com (price)", "data_file": "/data/homes.json"})
        return rows

    def history(self) -> list[dict]:
        rows = []
        for year, day, usd in self.january_prices():
            rows.append({"year": year, "date": long_date(day), "usd_text": fmt_money(usd), "sats_text": fmt_sats(1e8 / usd), "sats": 1e8 / usd})
        if self.price_daily:
            day, usd = self.price_daily[-1]
            rows.append({"year": "latest", "date": long_date(day), "usd_text": fmt_money(usd), "sats_text": fmt_sats(1e8 / usd), "sats": 1e8 / usd})
        return rows

    def network_summary(self) -> dict:
        out = {"fees": self.fees}
        if self.network:
            day, ths = self.network[-1]
            ago = _year_ago(self.network, day)
            out.update({"hashrate_ehs": ths / 1e6, "hashrate_text": f"{ths / 1e6:,.0f} EH/s", "hashrate_date": long_date(day),
                        "hashrate_ago_text": f"{ago[1] / 1e6:,.0f} EH/s" if ago else ""})
        return out

    def featured_basket(self) -> list[dict]:
        """The home page's mix of everyday prices: the FEATURED_ITEMS that have current data, in that order."""
        rows = {row["stem"]: row for row in self.basket()}
        return [rows[stem] for stem in FEATURED_ITEMS if stem in rows]

    def basket_groups(self) -> list[dict]:
        """The everyday prices grouped for the full table: food, home and energy, transport, drinks."""
        rows = self.basket()
        out = []
        for key, label in ITEM_GROUPS.items():
            group = [row for row in rows if row.get("group") == key]
            if group:
                out.append({"key": key, "label": label, "rows": group})
        return out

    def home_compare(self) -> dict | None:
        """The home page's first-screen comparison: a dollar, a dozen eggs, and a new home, each at its latest period
        and at the same period one and five years earlier. Every pair uses one series definition (daily averages for
        the dollar, monthly averages for eggs, quarterly figures for homes), so the latest quote is kept apart: it shows
        only in the Today view, labeled "Latest price" with its time. A row is left out when its data is missing."""
        rows = []

        def shown(text: str) -> float:
            """The number a reader sees in a formatted figure ("3,294 sats" is 3294, "5.72 bitcoin" is 5.72)."""
            return float(re.sub(r"[^0-9.]", "", text.split(" ")[0]))

        def entry(key, when_now, value_now, text_now, earlier, missing=None):
            """One row. A change is worked out from the two figures as printed, so the percentage beside them is the
            one a reader gets with a calculator; the bars are drawn from the same two numbers."""
            meta = COMPARE_ROWS[key]
            row = {"key": key, **meta, "now": {"when": when_now, "value": value_now, "text": text_now}}
            now = shown(text_now)
            for span, point in earlier.items():
                if not point:
                    continue
                when, _value, text = point
                then = shown(text)
                if not then or not now:
                    continue
                top = max(then, now)
                change = (now / then - 1) * 100
                if abs(change) < 0.5:
                    words = f"About the same {meta['unit']} {meta['per']}"
                else:
                    words = f"{pct_text(change)} {meta['more'] if change > 0 else meta['fewer']} {meta['per']}"
                row[span] = {"when": when, "value": then, "text": text, "change": change, "change_text": words,
                             "now_f": round(now / top, 4), "then_f": round(then / top, 4)}
            for span, when in (missing or {}).items():
                if span not in row:
                    row[span] = {"missing": COMPARE_MISSING.format(when=when)}
            return row

        def period_back(day: str, years: int) -> str:
            """The first day of the same month, that many years earlier (monthly and quarterly series are dated so)."""
            return f"{int(day[:4]) - years:04d}{day[4:]}"

        # A dollar: sats per dollar from the daily average price
        if self.price_daily and self.price_daily[-1][1]:
            day, usd = self.price_daily[-1]
            earlier = {}
            for span, cfg in COMPARE_SPANS.items():
                point = _years_ago(self.price_daily, day, cfg["years"])
                if point and point[1]:
                    earlier[span] = (short_date(point[0]), 1e8 / point[1], fmt_sats(1e8 / point[1]))
            rows.append(entry("dollar", short_date(day), 1e8 / usd, fmt_sats(1e8 / usd), earlier))

        # A dozen eggs: the BLS monthly average over the month's average bitcoin price
        eggs = self.items_data.get("eggs")
        if eggs:
            day, usd = eggs["points"][-1]
            btc = self.monthly_avg.get(day)
            if btc:
                earlier, missing = {}, {}
                first = eggs["points"][0][0]
                for span, cfg in COMPARE_SPANS.items():
                    wanted = period_back(day, cfg["years"])
                    point = _on_or_before(eggs["points"], wanted)
                    if point and point[0] == wanted and point[1] and self.monthly_avg.get(point[0]):     # the same month, that many years back
                        sats = point[1] / self.monthly_avg[point[0]] * 1e8
                        earlier[span] = (short_month(point[0]), sats, fmt_sats(sats))
                    elif wanted >= first:          # inside the series, but the source skipped that month
                        missing[span] = short_month(wanted)
                sats_now = usd / btc * 1e8
                rows.append(entry("eggs", short_month(day), sats_now, fmt_sats(sats_now), earlier, missing))

        # A new home: the quarterly median new-home price over the quarter's average bitcoin price
        if self.homes:
            day, usd = self.homes[-1]
            btc = self.quarterly_avg.get(day)
            if btc:
                earlier, missing = {}, {}
                first = self.homes[0][0]
                for span, cfg in COMPARE_SPANS.items():
                    wanted = period_back(day, cfg["years"])
                    point = _on_or_before(self.homes, wanted)
                    if point and point[0] == wanted and point[1] and self.quarterly_avg.get(point[0]):
                        coins = point[1] / self.quarterly_avg[point[0]]
                        earlier[span] = (quarter(point[0]), coins, fmt_btc(coins))
                    elif wanted >= first:
                        missing[span] = quarter(wanted)
                rows.append(entry("home", quarter(day), usd / btc, fmt_btc(usd / btc), earlier, missing))

        if not rows:
            return None
        takeaways = {"today": TAKEAWAY_TODAY}
        dollar = next((row for row in rows if row["key"] == "dollar"), None)
        for span, cfg in COMPARE_SPANS.items():
            point = dollar.get(span) if dollar else None
            if not point or "change" not in point:
                continue
            if abs(point["change"]) < 0.5:
                takeaways[span] = TAKEAWAY_SAME.format(earlier=cfg["earlier"])
            else:
                takeaways[span] = (TAKEAWAY_MORE if point["change"] > 0 else TAKEAWAY_FEWER).format(pct=pct_text(point["change"]), earlier=cfg["earlier"])
        # a view is offered when at least one row has both of its figures for it
        spans = [{"key": span, **cfg} for span, cfg in COMPARE_SPANS.items() if any("change" in row.get(span, {}) for row in rows)]
        return {"rows": rows, "spans": spans, "takeaways": takeaways}

    # ------------------------------------------------------------------ programmatic "in sats" pages

    def amount_pages(self) -> list[dict]:
        pages = []
        januaries = self.january_prices()
        for cur, meta in CURRENCIES.items():
            price = self.prices.get(cur)
            if not price:
                continue
            for amount in AMOUNTS:
                sats = amount / price * 1e8
                btc = amount / price
                money = f"{meta['symbol']}{amount:,}"
                sats_text = fmt_sats(sats)
                nearby = [a for a in AMOUNTS if a != amount and abs(AMOUNTS.index(a) - AMOUNTS.index(amount)) <= 4]
                yearly = []
                if cur == "usd":
                    for year, _day, usd in januaries:
                        yearly.append({"year": year, "sats": amount / usd * 1e8, "sats_text": fmt_sats(amount / usd * 1e8), "price_text": fmt_money(usd)})
                title = f"{money} in sats: {sats_text} today"
                pages.append({
                    "url": f"/sats/{amount}-{cur}/", "amount": amount, "currency": cur, "symbol": meta["symbol"], "currency_name": meta["name"],
                    "money": money, "sats": sats, "sats_text": sats_text, "btc_text": f"{btc:,.8f} BTC",   # eight places, the way live.js rewrites it
                    "price_text": fmt_money(price, meta["symbol"]),
                    "title": title if len(title) <= 60 else f"{money} in sats today",
                    "heading": f"How many sats does {money} buy?",
                    "description": (f"See how many sats {money} equals at the latest checked bitcoin price, plus its January history since {januaries[0][0]}."
                                    if yearly else
                                    f"See how many sats {money} equals at the latest checked bitcoin price in {meta['name']}, with links to amounts in other currencies."),
                    "nearby": [{"amount": a, "money": f"{meta['symbol']}{a:,}", "sats_text": fmt_sats(a / price * 1e8), "url": f"/sats/{a}-{cur}/"} for a in nearby],
                    "other_currencies": [{"currency": c, "money": f"{CURRENCIES[c]['symbol']}{amount:,}", "url": f"/sats/{amount}-{c}/"} for c in CURRENCIES if c != cur and self.prices.get(c)],
                    "yearly": yearly,
                })
        return pages

    def amount_index(self) -> list[dict]:
        out = []
        for cur, meta in CURRENCIES.items():
            price = self.prices.get(cur)
            if not price:
                continue
            out.append({"currency": cur, "name": meta["name"], "symbol": meta["symbol"], "sats_per_unit": fmt_sats(1e8 / price), "price_text": fmt_money(price, meta["symbol"]),
                        "amounts": [{"amount": a, "money": f"{meta['symbol']}{a:,}", "sats_text": fmt_sats(a / price * 1e8), "url": f"/sats/{a}-{cur}/"} for a in AMOUNTS]})
        return out

    def gallery(self) -> list[dict]:
        return self.charts

    def weekly_chart(self, entries, day: dt.date, start=None) -> dict | None:
        """The home page's chart of the week: `entries` (each a chart's slug and its line) take turns, one a week,
        starting again after the last. Weeks run Monday to Sunday and are counted from `start`, so the turn does not
        jump at New Year. An entry whose chart is missing gives its week to the next one."""
        listed = [entry for entry in entries or [] if isinstance(entry, dict) and entry.get("slug")]
        if not listed:
            return None
        if not isinstance(start, dt.date):
            start = dt.date(2026, 9, 28)
        monday = start - dt.timedelta(days=start.weekday())
        week = (day - monday).days // 7
        for step in range(len(listed)):
            entry = listed[(week + step) % len(listed)]
            card = self.chart_by_slug.get(entry["slug"])
            if card:
                return {"card": card, "line": entry.get("line"), "slug": entry["slug"]}
        return None
