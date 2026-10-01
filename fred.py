"""FRED (Federal Reserve Bank of St. Louis) series observations.

Docs: https://fred.stlouisfed.org/docs/api/fred/series_observations.html
Shape: {"observations":[{"realtime_start":"...","realtime_end":"...","date":"2026-09-30","value":"7651.54"}, ...]}
A missing value is the string ".". Required attribution is in lib/site.py (ATTRIBUTION_LINES["fred"]).
Note: FRED's S&P 500 series carries the last 10 years only, by agreement with the index owner.
"""

from __future__ import annotations

import os

from .http import SourceError, get_json

SOURCE = {"name": "FRED, Federal Reserve Bank of St. Louis", "url": "https://fred.stlouisfed.org"}

SERIES = {
    "home_price": {"id": "MSPUS", "title": "Median sales price of new houses sold in the United States", "unit": "USD", "frequency": "quarterly"},
    "sp500": {"id": "SP500", "title": "S&P 500 index, daily close", "unit": "index", "frequency": "daily"},
}


def observations(series_id: str, start: str = "2010-01-01") -> list[tuple[str, float]]:
    key = os.environ.get("FRED_KEY", "").strip()
    if not key and os.environ.get("SATS_FIXTURES") != "1":
        raise SourceError("FRED: FRED_KEY is not set")
    body = get_json(
        "https://api.stlouisfed.org/fred/series/observations",
        params={"series_id": series_id, "api_key": key, "file_type": "json", "observation_start": start},
        fixture=f"fred_{series_id}.json",
    )
    if "observations" not in body:
        raise SourceError(f"FRED {series_id}: " + str(body.get("error_message") or body)[:200])
    points = []
    for row in body["observations"]:
        value = row.get("value", ".")
        if value in (".", "", None):
            continue
        try:
            points.append((row["date"], float(value)))
        except (KeyError, TypeError, ValueError):
            continue
    if not points:
        raise SourceError(f"FRED {series_id}: no observations")
    return sorted(points)


def all_series() -> dict[str, list[tuple[str, float]]]:
    out = {}
    for name, spec in SERIES.items():
        out[name] = observations(spec["id"])
    return out
