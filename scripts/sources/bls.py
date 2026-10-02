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

from .http import SourceError, fixtures_on, post_json

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
    # More everyday items for the Items in sats pages (step 17). A series BLS no longer publishes is skipped.
    "bananas": {"id": "APU0000711211", "title": "Bananas, per pound, U.S. city average", "unit": "USD per pound"},
    "chicken": {"id": "APU0000706111", "title": "Chicken, fresh, whole, per pound, U.S. city average", "unit": "USD per pound"},
    "bacon": {"id": "APU0000704111", "title": "Bacon, sliced, per pound, U.S. city average", "unit": "USD per pound"},
    "flour": {"id": "APU0000701111", "title": "Flour, white, all purpose, per pound, U.S. city average", "unit": "USD per pound"},
    "rice": {"id": "APU0000701312", "title": "Rice, white, long grain, uncooked, per pound, U.S. city average", "unit": "USD per pound"},
    "sugar": {"id": "APU0000715211", "title": "Sugar, white, all sizes, per pound, U.S. city average", "unit": "USD per pound"},
    "butter": {"id": "APU0000FS1101", "title": "Butter, salted, grade AA, stick, per pound, U.S. city average", "unit": "USD per pound"},
    "potatoes": {"id": "APU0000712112", "title": "Potatoes, white, per pound, U.S. city average", "unit": "USD per pound"},
    "tomatoes": {"id": "APU0000712311", "title": "Tomatoes, field grown, per pound, U.S. city average", "unit": "USD per pound"},
    "oranges": {"id": "APU0000711311", "title": "Oranges, navel, per pound, U.S. city average", "unit": "USD per pound"},
    "apples": {"id": "APU0000711111", "title": "Apples, red delicious, per pound, U.S. city average", "unit": "USD per pound"},
    "wheat_bread": {"id": "APU0000702212", "title": "Bread, whole wheat, pan, per pound, U.S. city average", "unit": "USD per pound"},
    "diesel": {"id": "APU000074717", "title": "Automotive diesel fuel, per gallon, U.S. city average", "unit": "USD per gallon"},
    "premium_gas": {"id": "APU000074716", "title": "Gasoline, unleaded premium, per gallon, U.S. city average", "unit": "USD per gallon"},
    "natural_gas": {"id": "APU000072620", "title": "Utility (piped) gas, per therm, U.S. city average", "unit": "USD per therm"},
    "fuel_oil": {"id": "APU000072511", "title": "Fuel oil #2, per gallon, U.S. city average", "unit": "USD per gallon"},
    "beer": {"id": "APU0000720311", "title": "Malt beverages, all types, per 16 ounces, U.S. city average", "unit": "USD per 16 oz"},
    "wine": {"id": "APU0000720211", "title": "Wine, red and white table, per liter, U.S. city average", "unit": "USD per liter"},
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
