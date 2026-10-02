"""U.S. Bureau of Labor Statistics API v2: CPI and average consumer prices, monthly.

Docs: https://www.bls.gov/developers/api_signature_v2.htm
With a registration key: up to 50 series and 20 years per request, 500 requests a day; without one, 25 series and 10 years.
The request is split into batches of that size, so the list below can grow past the limit.
Shape: {"status":"REQUEST_SUCCEEDED","Results":{"series":[{"seriesID":"CUUR0000SA0",
        "data":[{"year":"2026","period":"M08","periodName":"August","value":"325.123","footnotes":[{}]}, ...]}]}}
Required attribution on pages that use this data is in lib/site.py (ATTRIBUTION_LINES["bls"]).
"""

from __future__ import annotations

import datetime as dt
import os

from lib.stats_data import ITEMS

from .http import SourceError, fixtures_on, post_json

SOURCE = {"name": "U.S. Bureau of Labor Statistics", "url": "https://www.bls.gov"}

# Series we keep. The key is the name used in data/ files; the id is BLS's. The everyday items come from the one
# table the site also reads (ITEMS in lib/stats_data.py), so a series is defined and named in a single place.
SERIES = {
    "cpi": {"id": "CUUR0000SA0", "title": "CPI-U, all items, U.S. city average, not seasonally adjusted", "unit": "index 1982-84=100"},
    **{name: {"id": item["id"], "title": item["title"], "unit": item["data_unit"]} for name, item in ITEMS.items()},
}

# BLS answers at most 50 series per request with a registration key and 25 without.
BATCH_WITH_KEY = 50
BATCH_WITHOUT_KEY = 25

MONTHS = {f"M{n:02d}": n for n in range(1, 13)}


def monthly(start_year: int = 2010, end_year: int | None = None) -> dict[str, list[tuple[str, float]]]:
    """Return {name: [(YYYY-MM-01, value), ...] oldest first} for every series in SERIES that BLS answered."""
    key = os.environ.get("BLS_KEY", "").strip()
    end_year = end_year or dt.date.today().year
    if not key:
        # Without a key BLS allows 10 years per request; trim rather than fail
        start_year = max(start_year, end_year - 9)
    ids = [spec["id"] for spec in SERIES.values()]
    batch = BATCH_WITH_KEY if key else BATCH_WITHOUT_KEY
    if fixtures_on():
        batch = max(len(ids), 1)  # the fixture holds every series in one answer
    by_id = {spec["id"]: name for name, spec in SERIES.items()}
    out: dict[str, list[tuple[str, float]]] = {}
    for n, start in enumerate(range(0, len(ids), batch)):
        payload = {
            "seriesid": ids[start:start + batch],
            "startyear": str(start_year),
            "endyear": str(end_year),
        }
        if key:
            payload["registrationkey"] = key
        body = post_json(
            "https://api.bls.gov/publicAPI/v2/timeseries/data/",
            payload,
            fixture="bls_monthly.json" if n == 0 else f"bls_monthly_{n}.json",
            headers={"content-type": "application/json"},
        )
        if body.get("status") != "REQUEST_SUCCEEDED":
            raise SourceError("BLS: " + "; ".join(body.get("message") or [body.get("status", "no status")]))
        for series in (body.get("Results") or {}).get("series") or []:
            name = by_id.get(series.get("seriesID"))
            if not name:
                continue
            points = []
            for row in series.get("data") or []:
                month = MONTHS.get(row.get("period", ""))
                if not month:
                    continue  # M13 is the annual average; skip it
                try:
                    points.append((f"{int(row['year']):04d}-{month:02d}-01", float(row["value"])))
                except (KeyError, TypeError, ValueError):
                    continue
            if points:
                out[name] = sorted(points)
    if not out:
        raise SourceError("BLS: no series in the answer")
    return out
