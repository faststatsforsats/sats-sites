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
from bisect import bisect_right
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CHARTS = ROOT / "charts"

START_YEAR = 2011

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

# Everyday items: data file stem -> how the pages talk about it. Items in data/ that are not listed here
# still get a page, named from the series title.
ITEMS = {
    "eggs": {"name": "A dozen eggs", "short": "a dozen large eggs", "unit": "per dozen", "chart": "eggs-in-sats"},
    "gasoline": {"name": "A gallon of gas", "short": "a gallon of regular gasoline", "unit": "per gallon"},
    "milk": {"name": "A gallon of milk", "short": "a gallon of whole milk", "unit": "per gallon"},
    "bread": {"name": "A loaf of bread", "short": "a pound of white bread", "unit": "per pound"},
    "coffee": {"name": "A pound of coffee", "short": "a pound of ground coffee", "unit": "per pound"},
    "ground_beef": {"name": "A pound of ground beef", "short": "a pound of ground beef", "unit": "per pound"},
    "electricity": {"name": "A kilowatt-hour of electricity", "short": "a kilowatt-hour of electricity", "unit": "per kWh"},
    "bananas": {"name": "A pound of bananas", "short": "a pound of bananas", "unit": "per pound"},
    "chicken": {"name": "A pound of chicken", "short": "a pound of fresh whole chicken", "unit": "per pound"},
    "bacon": {"name": "A pound of bacon", "short": "a pound of sliced bacon", "unit": "per pound"},
    "flour": {"name": "A pound of flour", "short": "a pound of all-purpose flour", "unit": "per pound"},
    "rice": {"name": "A pound of rice", "short": "a pound of long-grain rice", "unit": "per pound"},
    "sugar": {"name": "A pound of sugar", "short": "a pound of white sugar", "unit": "per pound"},
    "butter": {"name": "A pound of butter", "short": "a pound of salted butter", "unit": "per pound"},
    "potatoes": {"name": "A pound of potatoes", "short": "a pound of white potatoes", "unit": "per pound"},
    "tomatoes": {"name": "A pound of tomatoes", "short": "a pound of field-grown tomatoes", "unit": "per pound"},
    "oranges": {"name": "A pound of oranges", "short": "a pound of navel oranges", "unit": "per pound"},
    "apples": {"name": "A pound of apples", "short": "a pound of red delicious apples", "unit": "per pound"},
    "wheat_bread": {"name": "A loaf of whole wheat bread", "short": "a pound of whole wheat bread", "unit": "per pound"},
    "diesel": {"name": "A gallon of diesel", "short": "a gallon of diesel", "unit": "per gallon"},
    "premium_gas": {"name": "A gallon of premium gas", "short": "a gallon of premium gasoline", "unit": "per gallon"},
    "natural_gas": {"name": "A therm of natural gas", "short": "a therm of piped natural gas", "unit": "per therm"},
    "fuel_oil": {"name": "A gallon of heating oil", "short": "a gallon of No. 2 fuel oil", "unit": "per gallon"},
    "beer": {"name": "A pint of beer", "short": "16 ounces of malt beverage", "unit": "per 16 oz"},
    "wine": {"name": "A liter of wine", "short": "a liter of table wine", "unit": "per liter"},
}
NOT_ITEMS = {"cpi", "latest", "price-daily", "network", "fear-greed", "gold", "homes", "sp500"}


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


def _year_ago(series, day: str):
    d = dt.date.fromisoformat(day[:10])
    try:
        target = d.replace(year=d.year - 1)
    except ValueError:
        target = d.replace(year=d.year - 1, day=28)
    return _on_or_before(series, target.isoformat())


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
        self.fear_greed = self.latest.get("fear_greed")
        self.cpi = self.latest.get("cpi")
        self.network = _points(_read(root / "data" / "network.json"))
        self.gold = _points(_read(root / "data" / "gold.json"))
        self.homes = _points(_read(root / "data" / "homes.json"))
        self.sp500 = _points(_read(root / "data" / "sp500.json"))
        self.items_data = self._load_items()

        self.monthly_avg = self._monthly_average(self.price_daily)
        self.quarterly_avg = self._quarterly_average(self.price_daily)

    # ------------------------------------------------------------------ loading

    def _load_items(self) -> dict:
        out = {}
        for path in sorted((self.root / "data").glob("*.json")):
            if path.stem in NOT_ITEMS:
                continue
            payload = _read(path)
            points = _points(payload)
            if not points or "bls_series_id" not in (payload or {}):
                continue
            meta = ITEMS.get(path.stem) or {}
            title = payload["series"].get("name", path.stem)
            out[path.stem] = {
                "slug": slugify(path.stem.replace("_", "-")),
                "stem": path.stem,
                "name": meta.get("name") or title.split(",")[0].strip().capitalize(),
                "short": meta.get("short") or title.split(",")[0].strip().lower(),
                "unit": meta.get("unit") or payload["series"].get("unit", ""),
                "chart": meta.get("chart"),
                "series_title": title,
                "series_id": payload["bls_series_id"],
                "points": points,
                "data_file": f"/data/{path.name}",
            }
        return out

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
            ago = _year_ago(item["points"], day)
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
                "heading": f"{row['name']}, priced in sats",
                "description": f"What {row['short']} costs in sats this month and each January since 2011, from the BLS average price and the monthly average bitcoin price.",
                "finding": f"{row['name']} cost {row['sats_text']} in {row['month']}, at the U.S. city average price of {row['usd_text']} {row['unit']}.",
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
                ago = _year_ago(self.gold, day)
                ago_sats = ago[1] / self.monthly_avg[ago[0]] * 1e8 if ago and self.monthly_avg.get(ago[0]) else None
                rows.append({"name": "An ounce of gold", "when": month_name(day), "usd_text": fmt_money(usd), "value_text": fmt_sats(usd / btc * 1e8),
                             "ago_text": fmt_sats(ago_sats) if ago_sats else "", "chart": "gold-in-sats", "source": "World Bank Pink Sheet (gold), blockchain.com (price)", "data_file": "/data/gold.json"})
        if self.homes:
            day, usd = self.homes[-1]
            btc = self.quarterly_avg.get(day)
            if btc:
                ago = _year_ago(self.homes, day)
                ago_btc = ago[1] / self.quarterly_avg[ago[0]] if ago and self.quarterly_avg.get(ago[0]) else None
                rows.append({"name": "A median new home in the United States", "when": quarter(day), "usd_text": fmt_money(usd), "value_text": fmt_btc(usd / btc),
                             "ago_text": fmt_btc(ago_btc) if ago_btc else "", "chart": "home-in-bitcoin", "source": "FRED (MSPUS), blockchain.com (price)", "data_file": "/data/homes.json"})
        if self.sp500:
            day, level = self.sp500[-1]
            btc = self.price_on(day)
            if btc:
                ago = _year_ago(self.sp500, day)
                ago_btc_price = self.price_on(ago[0]) if ago else None
                ago_sats = ago[1] / ago_btc_price * 1e8 if ago and ago_btc_price else None
                rows.append({"name": "The S&P 500 index level", "when": long_date(day), "usd_text": f"{level:,.0f} points", "value_text": fmt_sats(level / btc * 1e8),
                             "ago_text": fmt_sats(ago_sats) if ago_sats else "", "chart": None, "source": "FRED (SP500), blockchain.com (price)", "data_file": "/data/sp500.json"})
        return rows

    def history(self) -> list[dict]:
        rows = []
        for year, day, usd in self.january_prices():
            rows.append({"year": year, "date": long_date(day), "usd_text": fmt_money(usd), "sats_text": fmt_sats(1e8 / usd), "sats": 1e8 / usd})
        if self.price_daily:
            day, usd = self.price_daily[-1]
            rows.append({"year": "now", "date": long_date(day), "usd_text": fmt_money(usd), "sats_text": fmt_sats(1e8 / usd), "sats": 1e8 / usd})
        return rows

    def network_summary(self) -> dict:
        out = {"fees": self.fees}
        if self.network:
            day, ths = self.network[-1]
            ago = _year_ago(self.network, day)
            out.update({"hashrate_ehs": ths / 1e6, "hashrate_text": f"{ths / 1e6:,.0f} EH/s", "hashrate_date": long_date(day),
                        "hashrate_ago_text": f"{ago[1] / 1e6:,.0f} EH/s" if ago else ""})
        return out

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
                    "money": money, "sats": sats, "sats_text": sats_text, "btc_text": f"{btc:,.8f} BTC".rstrip("0").rstrip("."),
                    "price_text": fmt_money(price, meta["symbol"]),
                    "title": title if len(title) <= 60 else f"{money} in sats today",
                    "heading": f"How many sats is {money}?",
                    "description": f"{money} is {sats_text} at today's price, with the live number, the price behind it, and what {money} bought in sats each January since 2011.",
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
