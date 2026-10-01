"""blockchain.com charts API: daily series since 2009, no key.

Docs: https://www.blockchain.com/explorer/charts (each chart has an API link).
Shape: {"status":"ok","name":"Market Price (USD)","unit":"USD","period":"day","description":"...",
        "values":[{"x":1788220800,"y":78549.65}, ...]}  with x a UTC unix timestamp.
"""

from __future__ import annotations

import datetime as dt

from .http import SourceError, get_json

SOURCE = {"name": "blockchain.com", "url": "https://www.blockchain.com/explorer/charts"}

CHARTS = {
    "market-price": {"title": "Market price", "unit": "USD", "page": "https://www.blockchain.com/explorer/charts/market-price"},
    "hash-rate": {"title": "Hash rate", "unit": "TH/s", "page": "https://www.blockchain.com/explorer/charts/hash-rate"},
    "difficulty": {"title": "Difficulty", "unit": "", "page": "https://www.blockchain.com/explorer/charts/difficulty"},
    "n-transactions": {"title": "Confirmed transactions per day", "unit": "transactions", "page": "https://www.blockchain.com/explorer/charts/n-transactions"},
}


def chart(name: str, timespan: str = "all") -> list[tuple[str, float]]:
    """Return [(YYYY-MM-DD, value), ...] oldest first."""
    if name not in CHARTS:
        raise SourceError(f"unknown blockchain.com chart {name}")
    body = get_json(
        f"https://api.blockchain.info/charts/{name}",
        params={"timespan": timespan, "format": "json", "sampled": "false"},
        fixture=f"blockchain_{name}.json",
    )
    values = body.get("values") or []
    if not values:
        raise SourceError(f"blockchain.com {name}: empty answer")
    points = []
    for item in values:
        try:
            day = dt.datetime.fromtimestamp(int(item["x"]), dt.timezone.utc).date().isoformat()
            points.append((day, float(item["y"])))
        except (KeyError, TypeError, ValueError):
            continue
    points.sort()
    # One value per day (the API already does this; keep the last if it ever repeats)
    deduped: dict[str, float] = {}
    for day, value in points:
        deduped[day] = value
    return sorted(deduped.items())
