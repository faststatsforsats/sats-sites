"""FRED (Federal Reserve Bank of St. Louis) series observations.

Docs: https://fred.stlouisfed.org/docs/api/fred/series_observations.html
Shape: {"observations":[{"realtime_start":"...","realtime_end":"...","date":"2026-09-30","value":"7651.54"}, ...]}
A missing value is the string ".". Required attribution is in lib/site.py (ATTRIBUTION_LINES["fred"]).

Before adding a series, open its page on fred.stlouisfed.org and read the notes. FRED's API terms say a series owned
by a third party needs the owner's permission for anything beyond personal use. The S&P 500 (SP500) is one: it belongs
to S&P Dow Jones Indices, and its page says it may not be reproduced without S&P's written permission. It was fetched
here until October 2, 2026 and came off at Jim's call until S&P answers (see WITHDRAWN_DATA in lib/stats_data.py).
MSPUS, the new-home price, comes from the Census Bureau and HUD.
"""

from __future__ import annotations

import os

from .http import SourceError, get_json

SOURCE = {"name": "FRED, Federal Reserve Bank of St. Louis", "url": "https://fred.stlouisfed.org"}

SERIES = {
    "home_price": {"id": "MSPUS", "title": "Median sales price of new houses sold in the United States", "unit": "USD", "frequency": "quarterly"},
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
