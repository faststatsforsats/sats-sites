"""alternative.me Crypto Fear & Greed Index: daily since February 2018, no key.

Docs: https://alternative.me/crypto/fear-and-greed-index/ (API section).
Shape: {"name":"Fear and Greed Index","data":[{"value":"74","value_classification":"Greed","timestamp":"1790812800"}, ...]}
limit=0 returns the whole history, newest first.
"""

from __future__ import annotations

import datetime as dt

from .http import SourceError, get_json

SOURCE = {"name": "alternative.me", "url": "https://alternative.me/crypto/fear-and-greed-index/"}


def history() -> list[tuple[str, int, str]]:
    """Return [(YYYY-MM-DD, value, label), ...] oldest first."""
    body = get_json("https://api.alternative.me/fng/", params={"limit": 0, "format": "json"}, fixture="alternative_fng.json")
    rows = body.get("data") or []
    if not rows:
        raise SourceError("alternative.me: empty answer")
    points = []
    for row in rows:
        try:
            day = dt.datetime.fromtimestamp(int(row["timestamp"]), dt.timezone.utc).date().isoformat()
            points.append((day, int(row["value"]), str(row.get("value_classification", ""))))
        except (KeyError, TypeError, ValueError):
            continue
    points.sort()
    return points
