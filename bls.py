"""U.S. Bureau of Labor Statistics API v2: CPI and average consumer prices, monthly.

Docs: https://www.bls.gov/developers/api_signature_v2.htm
With a registration key: up to 50 series and 20 years per request, 500 requests a day.
Shape: {"status":"REQUEST_SUCCEEDED","Results":{"series":[{"seriesID":"CUUR0000SA0",
        "data":[{"year":"2026","period":"M08","periodName":"August","value":"325.123","footnotes":[{}]}, ...]}]}}
Required attribution on pages that use this data is in lib/site.py (ATTRIBUTION_LINES["bls"]).
"""

from __future__ import annotations

import datetime as dt
import os

from .http import SourceError, post_json

SOURCE = {"name": "U.S. Bureau of Labor Statistics", "url": "https://www.bls.gov"}

# Series we keep. The key is the name used in data/ files; the id is BLS's.
SERIES = {
    "cpi": {"id": "CUUR0000SA0", "title": "CPI-U, all items, U.S. city average, not seasonally adjusted", "unit": "index 1982-84=100"},
    "eggs": {"id": "APU0000708111", "title": "Eggs, grade A, large, per dozen, U.S. city average", "unit": "USD per dozen"},
    "gasoline": {"id": "APU000074714", "title": "Gasoline, unleaded regular, per gallon, U.S. city average", "unit": "USD per gallon"},
    "ground_beef": {"id": "APU0000703112", "title": "Ground beef, 100% beef, per pound, U.S. city average", "unit": "USD per pound"},
    "milk": {"id": "APU0000709112", "title": "Milk, fresh, whole, fortified, per gallon, U.S. city average", "unit": "USD per gallon"},
    "bread": {"id": "APU0000702111", "title": "Bread, white, pan, per pound, U.S. city average", "unit": "USD per pound"},
    "coffee": {"id": "APU0000717311", "title": "Coffee, 100% ground roast, per pound, U.S. city average", "unit": "USD per pound"},
    "electricity": {"id": "APU000072610", "title": "Electricity, per kilowatt-hour, U.S. city average", "unit": "USD per kWh"},
}

MONTHS = {f"M{n:02d}": n for n in range(1, 13)}


def monthly(start_year: int = 2010, end_year: int | None = None) -> dict[str, list[tuple[str, float]]]:
    """Return {name: [(YYYY-MM-01, value), ...] oldest first} for every series in SERIES that BLS answered."""
    key = os.environ.get("BLS_KEY", "").strip()
    end_year = end_year or dt.date.today().year
    payload = {
        "seriesid": [spec["id"] for spec in SERIES.values()],
        "startyear": str(start_year),
        "endyear": str(end_year),
    }
    if key:
        payload["registrationkey"] = key
    else:
        # Without a key BLS allows 10 years per request; trim rather than fail
        payload["startyear"] = str(max(start_year, end_year - 9))
    body = post_json(
        "https://api.bls.gov/publicAPI/v2/timeseries/data/",
        payload,
        fixture="bls_monthly.json",
        headers={"content-type": "application/json"},
    )
    if body.get("status") != "REQUEST_SUCCEEDED":
        raise SourceError("BLS: " + "; ".join(body.get("message") or [body.get("status", "no status")]))
    by_id = {spec["id"]: name for name, spec in SERIES.items()}
    out: dict[str, list[tuple[str, float]]] = {}
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
