"""The site's own live-data Worker (api.faststatsforsats.com): today's price in 30 currencies and the fee tiers.

The Worker already carries CoinGecko's attribution, so the Daily Build needs no CoinGecko key of its own.
"""

from __future__ import annotations

import os

from .http import get_json

API = os.environ.get("SITE_API", "https://api.faststatsforsats.com").rstrip("/")


def price() -> dict:
    return get_json(f"{API}/price", fixture="live_price.json")


def fees() -> dict:
    return get_json(f"{API}/fees", fixture="live_fees.json")
