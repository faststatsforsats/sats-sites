"""Helpers for date-indexed series: [(YYYY-MM-DD, value), ...] oldest first."""

from __future__ import annotations

import datetime as dt
from bisect import bisect_right
from collections import defaultdict

Series = list[tuple[str, float]]


def parse(day: str) -> dt.date:
    return dt.date.fromisoformat(day[:10])


def latest(series: Series) -> tuple[str, float]:
    if not series:
        raise ValueError("empty series")
    return series[-1]


def value_on_or_before(series: Series, day: str) -> tuple[str, float] | None:
    """The last point dated on or before `day`."""
    days = [d for d, _ in series]
    idx = bisect_right(days, day)
    return series[idx - 1] if idx else None


def value_about(series: Series, years: int = 0, months: int = 0, days: int = 0) -> tuple[str, float] | None:
    """The point closest before `latest - offset`."""
    end = parse(series[-1][0])
    target_year = end.year - years
    target_month = end.month - months
    while target_month < 1:
        target_month += 12
        target_year -= 1
    day = min(end.day, 28)
    target = dt.date(target_year, target_month, day) - dt.timedelta(days=days)
    if target < parse(series[0][0]):
        return None
    return value_on_or_before(series, target.isoformat())


def since(series: Series, start: str) -> Series:
    return [(d, v) for d, v in series if d >= start]


def monthly_average(series: Series) -> Series:
    """Average a daily series by calendar month: [(YYYY-MM-01, mean), ...]."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for day, value in series:
        buckets[day[:7] + "-01"].append(value)
    return sorted((month, sum(values) / len(values)) for month, values in buckets.items())


def quarterly_average(series: Series) -> Series:
    """Average a daily series by calendar quarter, dated the first day of the quarter (FRED's convention)."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for day, value in series:
        d = parse(day)
        q_month = 3 * ((d.month - 1) // 3) + 1
        buckets[f"{d.year:04d}-{q_month:02d}-01"].append(value)
    return sorted((q, sum(values) / len(values)) for q, values in buckets.items())


def ratio(numerator: Series, denominator: Series, scale: float = 1.0) -> Series:
    """numerator / denominator on the dates both have, times scale."""
    denom = dict(denominator)
    out = []
    for day, value in numerator:
        base = denom.get(day)
        if base:
            out.append((day, value / base * scale))
    return out


def sats_per_unit(price_series: Series, usd_per_unit: Series) -> Series:
    """How many sats one unit (a dozen eggs, an ounce of gold) costs: usd_per_unit / (btc_usd / 1e8)."""
    price = dict(price_series)
    out = []
    for day, usd in usd_per_unit:
        btc_usd = price.get(day)
        if btc_usd:
            out.append((day, usd / btc_usd * 100_000_000))
    return out


def to_json(series: Series, digits: int = 2, significant: int | None = None) -> list[list]:
    """Rows for a data file. `digits` rounds to decimal places; `significant` rounds to that many significant figures
    instead, for a series that spans many orders of magnitude (hash rate: fractions of a terahash in 2009, hundreds of
    millions now), so its small early values are not saved as zero."""
    if significant:
        return [[day, float(f"{value:.{significant}g}")] for day, value in series]
    return [[day, round(value, digits)] for day, value in series]


def from_json(rows: list[list]) -> Series:
    return [(str(day), float(value)) for day, value in rows]


def fmt_int(value: float) -> str:
    return f"{value:,.0f}"


def fmt_usd(value: float) -> str:
    if value >= 1000:
        return f"${value:,.0f}"
    if value >= 10:
        return f"${value:,.2f}"
    return f"${value:,.2f}"


def long_date(day: str) -> str:
    d = parse(day)
    return f"{d:%B} {d.day}, {d.year}"


def month_name(day: str) -> str:
    d = parse(day)
    return f"{d:%B} {d.year}"


def pct_change(new: float, old: float) -> float:
    return (new / old - 1.0) * 100.0 if old else 0.0
