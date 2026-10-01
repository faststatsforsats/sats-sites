"""The charts the Daily Build draws, one function each, all through lib/chartstyle.

Each builder gets the fetched data (see daily_build.collect) and returns a dict for charts/index.json:
    slug, title (the finding, for the image), heading (the page H1), description (meta, under 155 chars),
    subtitle, unit, latest {date, value, text}, table [[label, date, text], ...],
    data_file, attribution [codes], sources [{name, url}], frequency
A builder returns None when the data it needs is missing, so one dead source never stops the others.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from lib.chartstyle import date_axis, label_last_point, render_chart, thousands
from scripts import series as S
from scripts.sources import alternative_me, blockchain_com, worldbank

START = "2011-01-01"
STATS_URL = "https://faststatsforsats.com"


def _log_axis(ax, unit_label: str) -> None:
    import matplotlib.ticker as mt

    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: thousands(v)))
    ax.yaxis.set_minor_formatter(mt.NullFormatter())
    ax.set_ylabel(unit_label)
    ax.grid(True, which="major", axis="y")


def _dates(series: S.Series) -> list[dt.date]:
    return [S.parse(d) for d, _ in series]


def _line(ax, c, series: S.Series, label_text: str, slot: int = 0) -> None:
    xs, ys = _dates(series), [v for _, v in series]
    ax.plot(xs, ys, color=c.series[slot], linewidth=1.6 if len(series) > 2000 else 2)
    date_axis(ax)
    label_last_point(ax, xs[-1], ys[-1], label_text, c, c.series[slot])


def _quarter(day: str) -> str:
    d = S.parse(day)
    return f"Q{(d.month - 1) // 3 + 1} {d.year}"


WHEN = {"daily": S.long_date, "monthly": S.month_name, "quarterly": _quarter}


def _table(series: S.Series, fmt, labels=(("now", {}), ("a year ago", {"years": 1}), ("five years ago", {"years": 5}), ("ten years ago", {"years": 10})), frequency: str = "daily") -> list[list[str]]:
    when = WHEN.get(frequency, S.long_date)
    rows = []
    for label, offset in labels:
        point = series[-1] if not offset else S.value_about(series, **offset)
        if point:
            rows.append([label, when(point[0]), fmt(point[1])])
    return rows


# ---------------------------------------------------------------- 1. sats per dollar

def sats_per_dollar(data, out_dir: Path, pulled: str):
    price = data.get("price_daily")
    if not price:
        return None
    series = [(d, 100_000_000 / p) for d, p in S.since(price, START) if p > 0]
    day, sats = series[-1]
    title = f"A dollar bought {sats:,.0f} sats on {S.long_date(day)}"

    def draw(ax, c):
        _line(ax, c, series, f"{sats:,.0f}")
        _log_axis(ax, "sats per US dollar (log scale)")

    render_chart("sats-per-dollar", title, draw, "blockchain.com market price", pulled, out_dir,
                 subtitle="Sats one US dollar buys, from the daily average bitcoin price, since 2011")
    return {
        "slug": "sats-per-dollar", "title": title,
        "heading": "Sats per dollar since 2011",
        "description": "How many sats one US dollar buys, every day since 2011, drawn from the daily average bitcoin price and updated each morning.",
        "subtitle": "Sats one US dollar buys, daily since 2011", "unit": "sats per dollar",
        "latest": {"date": day, "value": round(sats), "text": f"{sats:,.0f} sats"},
        "table": _table(series, lambda v: f"{v:,.0f} sats"),
        "data_file": "/data/price-daily.json", "frequency": "daily",
        "attribution": ["blockchain"], "sources": [{"name": "blockchain.com, market price (USD)", "url": blockchain_com.CHARTS["market-price"]["page"]}],
    }


# ---------------------------------------------------------------- 2. price in dollars

def price_usd(data, out_dir: Path, pulled: str):
    price = data.get("price_daily")
    if not price:
        return None
    series = S.since(price, START)
    day, usd = series[-1]
    title = f"One bitcoin cost {S.fmt_usd(usd)} on {S.long_date(day)}"

    def draw(ax, c):
        _line(ax, c, series, S.fmt_usd(usd))
        _log_axis(ax, "US dollars per bitcoin (log scale)")

    render_chart("price-usd", title, draw, "blockchain.com market price", pulled, out_dir,
                 subtitle="Daily average price across major exchanges, since 2011")
    return {
        "slug": "price-usd", "title": title,
        "heading": "Bitcoin price in dollars since 2011",
        "description": "The daily average bitcoin price in US dollars since 2011, on a log scale so early years stay readable, updated every morning.",
        "subtitle": "US dollars per bitcoin, daily since 2011", "unit": "USD",
        "latest": {"date": day, "value": round(usd, 2), "text": S.fmt_usd(usd)},
        "table": _table(series, S.fmt_usd),
        "data_file": "/data/price-daily.json", "frequency": "daily",
        "attribution": ["blockchain"], "sources": [{"name": "blockchain.com, market price (USD)", "url": blockchain_com.CHARTS["market-price"]["page"]}],
    }


# ---------------------------------------------------------------- 3. a dozen eggs in sats

def eggs_in_sats(data, out_dir: Path, pulled: str):
    price, eggs = data.get("price_daily"), (data.get("bls") or {}).get("eggs")
    if not price or not eggs:
        return None
    series = S.sats_per_unit(S.monthly_average(price), S.since(eggs, START))
    if len(series) < 12:
        return None
    day, sats = series[-1]
    title = f"A dozen eggs cost {sats:,.0f} sats in {S.month_name(day)}"

    def draw(ax, c):
        _line(ax, c, series, f"{sats:,.0f}", slot=1)
        _log_axis(ax, "sats per dozen (log scale)")

    render_chart("eggs-in-sats", title, draw, "U.S. Bureau of Labor Statistics (eggs), blockchain.com (price)", pulled, out_dir,
                 subtitle="Sats for a dozen grade A large eggs, U.S. city average, monthly since 2011")
    return {
        "slug": "eggs-in-sats", "title": title,
        "heading": "A dozen eggs priced in sats",
        "description": "What a dozen large eggs costs in sats each month since 2011, from the BLS average price and the monthly average bitcoin price.",
        "subtitle": "Sats per dozen eggs, monthly since 2011", "unit": "sats per dozen",
        "latest": {"date": day, "value": round(sats), "text": f"{sats:,.0f} sats"},
        "table": _table(series, lambda v: f"{v:,.0f} sats", frequency="monthly"),
        "data_file": "/data/eggs.json", "frequency": "monthly",
        "attribution": ["bls", "blockchain"],
        "sources": [{"name": "BLS average price, eggs, grade A, large, per dozen (APU0000708111)", "url": "https://data.bls.gov/timeseries/APU0000708111"},
                    {"name": "blockchain.com, market price (USD)", "url": blockchain_com.CHARTS["market-price"]["page"]}],
    }


# ---------------------------------------------------------------- 4. an ounce of gold in sats

def gold_in_sats(data, out_dir: Path, pulled: str):
    price, gold = data.get("price_daily"), data.get("gold_monthly")
    if not price or not gold:
        return None
    series = S.sats_per_unit(S.monthly_average(price), S.since(gold, START))
    if len(series) < 12:
        return None
    day, sats = series[-1]
    title = f"An ounce of gold cost {sats:,.0f} sats in {S.month_name(day)}"

    def draw(ax, c):
        _line(ax, c, series, f"{sats:,.0f}", slot=3)
        _log_axis(ax, "sats per troy ounce (log scale)")

    render_chart("gold-in-sats", title, draw, "World Bank Pink Sheet (gold), blockchain.com (price)", pulled, out_dir,
                 subtitle="Sats per troy ounce of gold, monthly average prices, since 2011")
    return {
        "slug": "gold-in-sats", "title": title,
        "heading": "Gold priced in sats",
        "description": "How many sats a troy ounce of gold costs, month by month since 2011, from the World Bank gold price and the average bitcoin price.",
        "subtitle": "Sats per troy ounce of gold, monthly since 2011", "unit": "sats per ounce",
        "latest": {"date": day, "value": round(sats), "text": f"{sats:,.0f} sats"},
        "table": _table(series, lambda v: f"{v:,.0f} sats", frequency="monthly"),
        "data_file": "/data/gold.json", "frequency": "monthly",
        "attribution": ["worldbank", "blockchain"],
        "sources": [{"name": "World Bank Commodity Price Data (The Pink Sheet), gold", "url": worldbank.SOURCE["url"]},
                    {"name": "blockchain.com, market price (USD)", "url": blockchain_com.CHARTS["market-price"]["page"]}],
    }


# ---------------------------------------------------------------- 5. a median new home in bitcoin

def home_in_bitcoin(data, out_dir: Path, pulled: str):
    price, homes = data.get("price_daily"), (data.get("fred") or {}).get("home_price")
    if not price or not homes:
        return None
    quarterly = dict(S.quarterly_average(price))
    series = [(d, usd / quarterly[d]) for d, usd in S.since(homes, START) if quarterly.get(d)]
    if len(series) < 8:
        return None
    day, btc = series[-1]
    q = (S.parse(day).month - 1) // 3 + 1
    when = f"Q{q} {S.parse(day).year}"
    title = f"A median new home cost {btc:,.1f} bitcoin in {when}"

    def draw(ax, c):
        _line(ax, c, series, f"{btc:,.1f}", slot=2)
        _log_axis(ax, "bitcoin per median new home (log scale)")

    render_chart("home-in-bitcoin", title, draw, "FRED (MSPUS), blockchain.com (price)", pulled, out_dir,
                 subtitle="Median sales price of new houses sold in the United States, in bitcoin, quarterly since 2011")

    def fmt(v):
        return f"{v:,.1f} bitcoin" if v >= 10 else f"{v:,.2f} bitcoin"

    return {
        "slug": "home-in-bitcoin", "title": title,
        "heading": "A new home priced in bitcoin",
        "description": "The median price of a new house sold in the United States, converted to bitcoin each quarter since 2011, from the Census Bureau figure on FRED.",
        "subtitle": "Bitcoin per median new home, quarterly since 2011", "unit": "bitcoin",
        "latest": {"date": day, "value": round(btc, 2), "text": fmt(btc)},
        "table": _table(series, fmt, frequency="quarterly"),
        "data_file": "/data/homes.json", "frequency": "quarterly",
        "attribution": ["fred", "blockchain"],
        "sources": [{"name": "FRED, Median Sales Price of New Houses Sold (MSPUS)", "url": "https://fred.stlouisfed.org/series/MSPUS"},
                    {"name": "blockchain.com, market price (USD)", "url": blockchain_com.CHARTS["market-price"]["page"]}],
    }


# ---------------------------------------------------------------- 6. fear and greed

def fear_greed(data, out_dir: Path, pulled: str):
    fng = data.get("fear_greed")
    if not fng:
        return None
    cutoff = (dt.date.today() - dt.timedelta(days=365)).isoformat()
    recent = [(d, float(v)) for d, v, _ in fng if d >= cutoff]
    if len(recent) < 30:
        return None
    day, value, label = fng[-1]
    title = f"Fear and Greed read {value} ({label}) on {S.long_date(day)}"

    def draw(ax, c):
        xs, ys = _dates(recent), [v for _, v in recent]
        for level, text in ((25, "extreme fear below 25"), (50, ""), (75, "extreme greed above 75")):
            ax.axhline(level, color=c.axis, linewidth=0.8, linestyle=(0, (3, 3)))
            if text:
                ax.text(xs[0], level + 1.5, text, fontsize=8, color=c.muted, va="bottom", bbox={"fc": c.surface, "ec": "none", "pad": 1.5})
        ax.plot(xs, ys, color=c.series[6], linewidth=2)
        ax.set_ylim(0, 100)
        ax.set_ylabel("index, 0 to 100")
        date_axis(ax)
        label_last_point(ax, xs[-1], ys[-1], f"{value} {label}", c, c.series[6])

    render_chart("fear-greed", title, draw, "alternative.me Crypto Fear & Greed Index", pulled, out_dir,
                 subtitle="Daily readings, last 12 months")
    labels = (("now", {}), ("a month ago", {"months": 1}), ("a year ago", {"years": 1}))
    simple = [(d, float(v)) for d, v, _ in fng]
    return {
        "slug": "fear-greed", "title": title,
        "heading": "The Fear and Greed gauge",
        "description": "The Crypto Fear & Greed Index from alternative.me, day by day for the last year, with what the reading means and how it is built.",
        "subtitle": "Crypto Fear & Greed Index, daily, last 12 months", "unit": "index",
        "latest": {"date": day, "value": value, "text": f"{value} ({label})"},
        "table": _table(simple, lambda v: f"{v:.0f}", labels),
        "data_file": "/data/fear-greed.json", "frequency": "daily",
        "attribution": ["altme"], "sources": [{"name": "alternative.me Crypto Fear & Greed Index", "url": alternative_me.SOURCE["url"]}],
    }


# ---------------------------------------------------------------- 7. hash rate

def hashrate(data, out_dir: Path, pulled: str):
    raw = data.get("hashrate_daily")
    if not raw:
        return None
    series = [(d, v / 1_000_000) for d, v in S.since(raw, START) if v > 0]   # TH/s -> EH/s
    day, ehs = series[-1]
    title = f"The network ran at {ehs:,.0f} EH/s on {S.long_date(day)}"

    def draw(ax, c):
        _line(ax, c, series, f"{ehs:,.0f} EH/s", slot=5)
        _log_axis(ax, "exahashes per second (log scale)")

    render_chart("hashrate", title, draw, "blockchain.com hash rate", pulled, out_dir,
                 subtitle="Estimated network hash rate, daily since 2011")
    return {
        "slug": "hashrate", "title": title,
        "heading": "Bitcoin hash rate since 2011",
        "description": "The estimated computing power securing Bitcoin, in exahashes per second, every day since 2011, on a log scale.",
        "subtitle": "Exahashes per second, daily since 2011", "unit": "EH/s",
        "latest": {"date": day, "value": round(ehs, 1), "text": f"{ehs:,.0f} EH/s"},
        "table": _table(series, lambda v: f"{v:,.1f} EH/s" if v < 10 else f"{v:,.0f} EH/s"),
        "data_file": "/data/network.json", "frequency": "daily",
        "attribution": ["blockchain"], "sources": [{"name": "blockchain.com, total hash rate", "url": blockchain_com.CHARTS["hash-rate"]["page"]}],
    }


BUILDERS = [sats_per_dollar, price_usd, eggs_in_sats, gold_in_sats, home_in_bitcoin, fear_greed, hashrate]
