"""The charts the Daily Build draws, one function each, all through lib/chartstyle.

Each builder gets the fetched data (see daily_build.collect) and returns a dict for charts/index.json:
    slug, title (the finding: drawn on the image, and the card's summary and the image's description for screen
    readers), heading (the page H1), description (meta, under 155 chars), subtitle (the line under the title on the
    image), unit, column (the heading over the figures in the page's small table), detail (the sentence that follows
    the finding in the paragraph under the image), lead (optional: the paragraph's first sentence when it should not
    be the title itself), credit (optional: a credit line that must sit beside the reading, as Markdown),
    latest {date, value, text}, table [[label, date, text], ...], data_file, attribution [codes],
    sources [{name, url}], frequency
The page titles, search descriptions, and every word a chart draws are Jim's own text (October 2026); change them
only from his edits, and change a chart page's title and description in its Markdown file too.
A builder returns None when the data it needs is missing, so one dead source never stops the others.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from lib.chartstyle import area_wash, date_axis, event_lines, glow_line, latest_pill, mark_point, remember_label, render_chart, thousands
from scripts import series as S
from scripts.sources import alternative_me, blockchain_com, worldbank

START = "2011-01-01"
STATS_URL = "https://faststatsforsats.com"

# Block 210,000, 420,000, 630,000, and 840,000 (dates in UTC)
HALVINGS = [dt.date(2012, 11, 28), dt.date(2016, 7, 9), dt.date(2020, 5, 11), dt.date(2024, 4, 20)]


def _short_date(day: str) -> str:
    d = S.parse(day)
    return f"{d.strftime('%b')} {d.day}, {d.year}"


def _extreme(series: S.Series, kind: str, since: str | None = None) -> tuple[str, float] | None:
    pool = [(d, v) for d, v in series if (since is None or d >= since)]
    if not pool:
        return None
    pick = min if kind == "min" else max
    return pick(pool, key=lambda p: p[1])


def _years_ago(series: S.Series, years: int) -> str:
    last = S.parse(series[-1][0])
    return last.replace(year=last.year - years).isoformat()


def _lower_side(series: S.Series, day: str) -> str:
    """Which side of a point the line runs lower on ("left" or "right"), so a label can sit over free space."""
    days = [d for d, _ in series]
    try:
        idx = days.index(day)
    except ValueError:
        return "right"
    window = max(3, len(series) // 12)
    left = [v for _, v in series[max(0, idx - window):idx]]
    right = [v for _, v in series[idx + 1:idx + 1 + window]]
    if not right:
        return "left"
    if not left:
        return "right"
    return "right" if sum(right) / len(right) < sum(left) / len(left) else "left"


def _draw_series(ax, c, series: S.Series, slot: int, latest_text: str, ylabel: str, marks=(), events_label: str | None = None, log: bool = True) -> None:
    """One series with the house look: thick glowing line, a wash beneath, dated event lines, marked extremes, the latest value as a pill."""
    import math

    xs, ys = _dates(series), [v for _, v in series]
    color = c.series[slot]
    if log:
        _log_axis(ax, ylabel)
    else:
        ax.set_ylabel(ylabel)
    glow_line(ax, xs, ys, color, c)
    date_axis(ax)
    ax.margins(x=0.01, y=0.18)
    if any(side == "below" for _, _, _, side in marks):
        # room under the line for a label beneath the lowest point
        lo, hi = ax.get_ylim()
        if log:
            llo, lhi = math.log10(lo), math.log10(hi)
            ax.set_ylim(10 ** (llo - 0.32 * (lhi - llo)), hi)
        else:
            ax.set_ylim(lo - 0.32 * (hi - lo), hi)
    area_wash(ax, xs, ys, color, c)
    if events_label:
        event_lines(ax, HALVINGS, "Halvings", c, where=events_label)
    latest_pill(ax, xs[-1], ys[-1], latest_text, color, c)   # first, so the marks keep clear of it
    import matplotlib.dates as mdates
    import numpy as np
    x0, x1 = ax.get_xlim()
    obstacles = ax.transData.transform(np.column_stack([mdates.date2num(xs), ys]))
    for day, value, text, side in marks:
        fx = (mdates.date2num(S.parse(day)) - x0) / (x1 - x0)
        if side == "above":
            lower = _lower_side(series, day)
            align = "left" if lower == "right" else "right"
            if fx > 0.78:
                align = "right"
            elif fx < 0.22:
                align = "left"
        else:
            align = "right" if fx > 0.5 else "left"
        mark_point(ax, S.parse(day), value, text, color, c, side=side, align=align, obstacles=obstacles)


def _sats_label(v: float) -> str:
    """25,056 sats, or 10.6M sats above a million (the exact figure is in the page's table)."""
    if v >= 1_000_000:
        return f"{v / 1_000_000:.3g}M sats" if v < 100_000_000 else f"{v / 1_000_000:,.0f}M sats"
    return f"{v:,.0f} sats"


def _short_month(day: str) -> str:
    d = S.parse(day)
    return f"{d.strftime('%b')} {d.year}"


def _value_marks(series: S.Series, fmt, when, low_word: str = "Low", peak_years: int = 5) -> list[tuple[str, float, str, str]]:
    """The all-time low (cheapest in sats) and the highest point of the last few years, skipping the latest point itself."""
    marks = []
    last_day = series[-1][0]
    since = _years_ago(series, peak_years)
    peak = _extreme(series, "max", since)
    low = _extreme(series, "min")
    if peak and peak[0] != last_day and (not low or peak[0] != low[0]):
        marks.append((peak[0], peak[1], f"High since {since[:4]}\n{fmt(peak[1])}, {when(peak[0])}", "above"))
    if low and low[0] != last_day:
        marks.append((low[0], low[1], f"{low_word}\n{fmt(low[1])}, {when(low[0])}", "below"))
    return marks


def _log_axis(ax, unit_label: str) -> None:
    import matplotlib.ticker as mt

    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: thousands(v)))
    ax.yaxis.set_minor_formatter(mt.NullFormatter())
    ax.set_ylabel(unit_label)
    ax.grid(True, which="major", axis="y")


def _dates(series: S.Series) -> list[dt.date]:
    return [S.parse(d) for d, _ in series]


def _quarter(day: str) -> str:
    d = S.parse(day)
    return f"Q{(d.month - 1) // 3 + 1} {d.year}"


WHEN = {"daily": S.long_date, "monthly": S.month_name, "quarterly": _quarter}


def _table(series: S.Series, fmt, labels=(("latest", {}), ("a year ago", {"years": 1}), ("five years ago", {"years": 5}), ("ten years ago", {"years": 10})), frequency: str = "daily") -> list[list[str]]:
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

    low = _extreme(series, "min")
    marks = []
    if low and low[0] != day:
        marks.append((low[0], low[1], f"Fewest ever\n{low[1]:,.0f} sats, {_short_date(low[0])}", "below"))

    def draw(ax, c):
        _draw_series(ax, c, series, 0, f"{sats:,.0f} sats", "sats per US dollar (log scale)", marks, events_label="bottom")

    render_chart("sats-per-dollar", title, draw, "blockchain.com market price", pulled, out_dir,
                 subtitle="Sats one US dollar buys, from the daily average bitcoin price, since 2011",
                 highlight=f"{sats:,.0f} sats", slot=0)
    return {
        "slug": "sats-per-dollar", "title": title,
        "heading": "Sats per dollar since 2011",
        "description": "See how many sats one US dollar bought each day since 2011, using the average bitcoin price. Read the chart and explore its source data.",
        "subtitle": "Sats one US dollar buys, from the daily average bitcoin price, since 2011", "unit": "sats per dollar",
        "column": "Sats per dollar",
        "detail": "Each point shows the sats one US dollar bought at that day's average bitcoin price.",
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

    high = _extreme(series, "max")
    marks = []
    if high and high[0] != day:
        marks.append((high[0], high[1], f"Highest daily average\n{S.fmt_usd(high[1])}, {_short_date(high[0])}", "above"))

    def draw(ax, c):
        _draw_series(ax, c, series, 0, S.fmt_usd(usd), "US dollars per bitcoin (log scale)", marks, events_label="top")

    render_chart("price-usd", title, draw, "blockchain.com market price", pulled, out_dir,
                 subtitle="Daily average price across major exchanges, since 2011",
                 highlight=S.fmt_usd(usd), slot=0)
    return {
        "slug": "price-usd", "title": title,
        "heading": "Bitcoin price in dollars since 2011",
        "description": "Track the daily average bitcoin price in US dollars since 2011. Learn how to read its logarithmic scale and compare dates in the data.",
        "subtitle": "Daily average price across major exchanges, since 2011", "unit": "USD",
        "column": "US dollars per bitcoin",
        "detail": "Each point shows the daily average bitcoin price in US dollars.",
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

    marks = _value_marks(series, _sats_label, _short_month)

    def draw(ax, c):
        _draw_series(ax, c, series, 1, f"{sats:,.0f} sats", "sats per dozen (log scale)", marks)

    render_chart("eggs-in-sats", title, draw, "U.S. Bureau of Labor Statistics (eggs), blockchain.com (price)", pulled, out_dir,
                 subtitle="Sats for a dozen grade A large eggs, U.S. city average, monthly since 2011",
                 highlight=f"{sats:,.0f} sats", slot=1)
    return {
        "slug": "eggs-in-sats", "title": title,
        "heading": "A dozen eggs priced in sats",
        "description": "See the sats cost of a dozen large eggs since 2011, using BLS monthly averages and bitcoin prices. Learn why both prices matter.",
        "subtitle": "Sats for a dozen grade A large eggs, U.S. city average, monthly since 2011", "unit": "sats per dozen",
        "column": "Sats per dozen",
        "detail": "Each point converts that month's average egg price to sats.",
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

    marks = _value_marks(series, _sats_label, _short_month)

    def draw(ax, c):
        _draw_series(ax, c, series, 3, f"{sats:,.0f} sats", "sats per troy ounce (log scale)", marks)

    render_chart("gold-in-sats", title, draw, "World Bank Pink Sheet (gold), blockchain.com (price)", pulled, out_dir,
                 subtitle="Sats per troy ounce of gold, monthly average prices, since 2011",
                 highlight=f"{sats:,.0f} sats", slot=3)
    return {
        "slug": "gold-in-sats", "title": title,
        "heading": "Gold priced in sats",
        "description": "Compare gold with bitcoin through the sats cost of a troy ounce since 2011, using monthly averages. See the method and source data.",
        "subtitle": "Sats per troy ounce of gold, monthly average prices, since 2011", "unit": "sats per ounce",
        "column": "Sats per troy ounce",
        "detail": "Each point converts that month's average gold price to sats.",
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
    def fmt(v):
        return f"{v:,.1f} bitcoin" if v >= 10 else f"{v:,.2f} bitcoin"

    title = f"A median new home cost {fmt(btc)} in {when}"   # the same figure, to the same precision, as the pill and the table

    marks = _value_marks(series, fmt, _quarter)

    def draw(ax, c):
        _draw_series(ax, c, series, 2, fmt(btc), "bitcoin per home (log scale)", marks)

    render_chart("home-in-bitcoin", title, draw, "FRED (MSPUS), blockchain.com (price)", pulled, out_dir,
                 subtitle="Median sales price of new houses sold in the United States, in bitcoin, quarterly since 2011",
                 highlight=fmt(btc), slot=2)

    return {
        "slug": "home-in-bitcoin", "title": title,
        "heading": "A new home priced in bitcoin",
        "description": "See the US median new-home price in bitcoin each quarter since 2011. Learn how the housing price and bitcoin price shape the line.",
        "subtitle": "Median sales price of new houses sold in the United States, in bitcoin, quarterly since 2011", "unit": "bitcoin",
        "column": "Bitcoin",
        "detail": "Each point converts that quarter's median new-home sale price to bitcoin.",
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

    high, low = _extreme(recent, "max"), _extreme(recent, "min")
    marks = []
    if high and high[0] != day:
        marks.append((high[0], high[1], f"Highest reading\n{high[1]:.0f}, {_short_date(high[0])}", "above"))
    if low and low[0] != day:
        marks.append((low[0], low[1], f"Lowest reading\n{low[1]:.0f}, {_short_date(low[0])}", "below"))

    def draw(ax, c):
        xs, ys = _dates(recent), [v for _, v in recent]
        color = c.series[6]
        ax.set_ylim(0, 100)
        ax.set_ylabel("index, 0 to 100")
        ax.axhspan(0, 25, color=c.critical, alpha=0.09, linewidth=0, zorder=0.5)
        ax.axhspan(75, 100, color=c.good, alpha=0.09, linewidth=0, zorder=0.5)
        tag = {"fc": c.surface, "ec": "none", "alpha": 0.75, "pad": 2}
        zone_tags = [
            ax.text(0.012, 0.125, "Extreme fear", transform=ax.transAxes, fontsize=10, color=c.muted, va="center", ha="left", zorder=4.5, bbox=tag),
            ax.text(0.012, 0.875, "Extreme greed", transform=ax.transAxes, fontsize=10, color=c.muted, va="center", ha="left", zorder=4.5, bbox=tag),
        ]
        renderer = ax.figure.canvas.get_renderer()
        for zone_tag in zone_tags:
            remember_label(ax, zone_tag.get_window_extent(renderer=renderer).padded(6))
        glow_line(ax, xs, ys, color, c, linewidth=2.6)
        date_axis(ax)
        ax.margins(x=0.01)
        latest_pill(ax, xs[-1], ys[-1], f"{value} ({label})", color, c)
        import matplotlib.dates as mdates
        import numpy as np
        obstacles = ax.transData.transform(np.column_stack([mdates.date2num(xs), ys]))
        for d, v, text, side in marks:
            mark_point(ax, S.parse(d), v, text, color, c, side=side, obstacles=obstacles)

    render_chart("fear-greed", title, draw, "alternative.me Crypto Fear & Greed Index", pulled, out_dir,
                 subtitle="Daily readings, last 12 months",
                 highlight=f"{value} ({label})", slot=6)
    labels = (("latest", {}), ("a month ago", {"months": 1}), ("a year ago", {"years": 1}))
    simple = [(d, float(v)) for d, v, _ in fng]
    return {
        "slug": "fear-greed", "title": title,
        "heading": "The Fear and Greed gauge",
        "description": "Follow alternative.me's daily Bitcoin Fear and Greed readings over the past year. Learn what the score measures, how it is built, and its limits.",
        "subtitle": "Daily readings, last 12 months", "unit": "index",
        "column": "Index score",
        "detail": f"The chart follows the Crypto Fear & Greed Index from [alternative.me]({alternative_me.SOURCE['url']}) each day over the last 12 months.",
        # alternative.me's terms: the credit sits right next to wherever the reading is displayed
        "credit": f"Source: [alternative.me]({alternative_me.SOURCE['url']})",
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
    title = f"Estimated hash rate was {ehs:,.0f} EH/s on {S.long_date(day)}"

    def hash_label(v, _=None):
        # The axis runs from gigahashes in 2011 to exahashes today; name each decade in its own unit
        if v >= 1000:
            return f"{v / 1000:g} ZH/s"
        if v >= 1:
            return f"{v:g} EH/s"
        if v >= 1e-3:
            return f"{v * 1e3:g} PH/s"
        if v >= 1e-6:
            return f"{v * 1e6:g} TH/s"
        return f"{v * 1e9:g} GH/s"

    record = _extreme(series, "max")
    marks = []
    if record and record[0] != day and (S.parse(day) - S.parse(record[0])).days > 45:
        marks.append((record[0], record[1], f"Record\n{record[1]:,.0f} EH/s, {_short_date(record[0])}", "above"))

    def draw(ax, c):
        import matplotlib.ticker as mt

        _draw_series(ax, c, series, 5, f"{ehs:,.0f} EH/s", "hash rate (log scale)", marks, events_label="top")
        ax.yaxis.set_major_formatter(mt.FuncFormatter(hash_label))

    render_chart("hashrate", title, draw, "blockchain.com hash rate", pulled, out_dir,
                 subtitle="Estimated network hash rate, daily since 2011",
                 highlight=f"{ehs:,.0f} EH/s", slot=5)
    return {
        "slug": "hashrate", "title": title,
        "heading": "Bitcoin hash rate since 2011",
        "description": "Explore Bitcoin's estimated hash rate since 2011. Learn what EH/s means, why daily readings vary, and what the chart can tell you.",
        "subtitle": "Estimated network hash rate, daily since 2011", "unit": "EH/s",
        "column": "EH/s",
        "lead": f"The estimated network hash rate was {ehs:,.0f} EH/s on {S.long_date(day)}.",
        "detail": "Each point shows the estimated mining calculations per second, in EH/s.",
        "latest": {"date": day, "value": round(ehs, 1), "text": f"{ehs:,.0f} EH/s"},
        "table": _table(series, lambda v: f"{v:,.1f} EH/s" if v < 10 else f"{v:,.0f} EH/s"),
        "data_file": "/data/network.json", "frequency": "daily",
        "attribution": ["blockchain"], "sources": [{"name": "blockchain.com, total hash rate", "url": blockchain_com.CHARTS["hash-rate"]["page"]}],
    }


# ---------------------------------------------------------------- 8. $25 a week since 2020

WEEKLY_START = "2020-01-06"   # the first Monday of 2020
WEEKLY_USD = 25.0


def twenty_five_a_week(data, out_dir: Path, pulled: str):
    """The campaign's hook chart: the sats a $25 buy every Monday since January 2020 added up to, week by week."""
    price = data.get("price_daily")
    if not price:
        return None
    by_day = dict(price)
    first, last = S.parse(WEEKLY_START), S.parse(price[-1][0])
    series: S.Series = []
    total_sats, buys = 0.0, 0
    monday = first
    while monday <= last:
        day = monday
        usd = by_day.get(day.isoformat())
        while not usd and day > first - dt.timedelta(days=7):   # a Monday with no published price: use the last known day
            day -= dt.timedelta(days=1)
            usd = by_day.get(day.isoformat())
        if usd and usd > 0:
            total_sats += WEEKLY_USD / usd * 100_000_000
            buys += 1
            series.append((monday.isoformat(), total_sats))
        monday += dt.timedelta(days=7)
    if len(series) < 52:
        return None
    day, sats = series[-1]
    spent = buys * WEEKLY_USD
    title = f"$25 a week since 2020 bought {sats:,.0f} sats"

    def fmt(v):
        return f"{v:,.0f} sats"

    # One mark: the week the stack passed its last halving (the line is monotonic, so highs and lows say nothing)
    marks = []
    for halving in reversed(HALVINGS):
        if halving > first:
            point = next(((d, v) for d, v in series if S.parse(d) >= halving), None)
            if point and point[0] != day:
                marks.append((point[0], point[1], f"{_sats_label(point[1])} by the\n{halving.year} halving", "above"))
            break

    def draw(ax, c):
        import matplotlib.ticker as mt

        _draw_series(ax, c, series, 1, _sats_label(sats), "sats stacked", marks, events_label="bottom", log=False)
        ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: thousands(v)))
        ax.set_ylim(0, ax.get_ylim()[1])
        ax.grid(True, which="major", axis="y")

    render_chart("twenty-five-a-week", title, draw, "blockchain.com market price", pulled, out_dir,
                 subtitle=f"$25 every Monday since January 2020 at that day's average price: {buys} buys, ${spent:,.0f} in all",
                 highlight=f"{sats:,.0f} sats", slot=1)
    labels = (("latest", {}), ("a year ago", {"years": 1}), ("three years ago", {"years": 3}), ("five years ago", {"years": 5}))
    return {
        "slug": "twenty-five-a-week", "title": title,
        "heading": "What $25 a week since 2020 bought in sats",
        "description": "See the sats a weekly 25-dollar bitcoin purchase since January 2020 would have accumulated. Historical example with the method and limits explained.",
        "subtitle": f"$25 every Monday since January 2020 at that day's average price: {buys} buys, ${spent:,.0f} in all", "unit": "sats stacked",
        "column": "Sats stacked",
        "detail": f"The line adds the sats from a modeled $25 purchase every Monday from {S.long_date(WEEKLY_START)}.",
        "latest": {"date": day, "value": round(sats), "text": fmt(sats), "spent": spent, "buys": buys},
        "table": _table(series, fmt, labels),
        "data_file": "/data/price-daily.json", "frequency": "weekly",
        "attribution": ["blockchain"], "sources": [{"name": "blockchain.com, market price (USD)", "url": blockchain_com.CHARTS["market-price"]["page"]}],
    }


BUILDERS = [sats_per_dollar, price_usd, eggs_in_sats, gold_in_sats, home_in_bitcoin, fear_greed, hashrate, twenty_five_a_week]
