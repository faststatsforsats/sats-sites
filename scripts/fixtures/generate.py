#!/usr/bin/env python3
"""Write synthetic fixtures for `python3 scripts/daily_build.py --fixtures`.

The numbers are made up (smooth curves with a little noise) and only mimic each source's shape, so the
pipeline can be exercised offline. They never reach the sites: a real run always goes to the network.
Run from the repository root: python3 scripts/fixtures/generate.py
"""

from __future__ import annotations

import datetime as dt
import io
import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
random.seed(42)
TODAY = dt.date.today()


def ts(day: dt.date) -> int:
    return int(dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc).timestamp())


def days(start: dt.date, step: int = 3):
    d = start
    while d <= TODAY:
        yield d
        d += dt.timedelta(days=step)


def price_on(day: dt.date) -> float:
    years = (day - dt.date(2010, 7, 18)).days / 365.25
    base = 0.07 * (1.75 ** years) * 20          # a long, slowing rise
    wobble = 1 + 0.35 * math.sin(years * 1.7) + random.uniform(-0.03, 0.03)
    return max(0.05, min(base * wobble, 90_000))


def write(name: str, payload) -> None:
    (HERE / name).write_text(json.dumps(payload) + "\n", encoding="utf-8")


# blockchain.com charts
prices = [{"x": ts(d), "y": round(price_on(d), 2)} for d in days(dt.date(2010, 7, 18))]
write("blockchain_market-price.json", {"status": "ok", "name": "Market Price (USD)", "unit": "USD", "period": "day", "description": "synthetic", "values": prices})
hashes = [{"x": ts(d), "y": round(1_000 * (1.9 ** ((d - dt.date(2010, 7, 18)).days / 365.25)) * random.uniform(0.9, 1.1), 1)} for d in days(dt.date(2010, 7, 18))]
write("blockchain_hash-rate.json", {"status": "ok", "name": "Hash Rate", "unit": "TH/s", "period": "day", "description": "synthetic", "values": hashes})

# alternative.me (newest first, strings)
fng = []
for d in days(dt.date(2018, 2, 1), step=1):
    v = int(50 + 30 * math.sin((d - dt.date(2018, 2, 1)).days / 23.0) + random.uniform(-8, 8))
    v = max(5, min(95, v))
    label = "Extreme Fear" if v < 25 else "Fear" if v < 46 else "Neutral" if v < 55 else "Greed" if v < 76 else "Extreme Greed"
    fng.append({"value": str(v), "value_classification": label, "timestamp": str(ts(d))})
write("alternative_fng.json", {"name": "Fear and Greed Index", "data": list(reversed(fng)), "metadata": {"error": None}})

# BLS (newest first, strings, M13 annual averages included to make sure they are skipped)
def bls_series(sid: str, start_value: float, yearly_growth: float):
    rows = []
    year, month = TODAY.year, TODAY.month - 1 or 12
    if TODAY.month == 1:
        year -= 1
    while year >= 2010:
        for m in range(month, 0, -1):
            months_back = (TODAY.year - year) * 12 + (TODAY.month - m)
            value = start_value * ((1 + yearly_growth) ** (-(months_back / 12))) * random.uniform(0.98, 1.02)
            rows.append({"year": str(year), "period": f"M{m:02d}", "periodName": dt.date(2000, m, 1).strftime("%B"), "value": f"{value:.3f}", "footnotes": [{}]})
        rows.append({"year": str(year), "period": "M13", "periodName": "Annual", "value": "0", "footnotes": [{}]})
        year -= 1
        month = 12
    return {"seriesID": sid, "data": rows}

write("bls_monthly.json", {"status": "REQUEST_SUCCEEDED", "responseTime": 100, "message": [], "Results": {"series": [
    bls_series("CUUR0000SA0", 325.0, 0.03), bls_series("APU0000708111", 3.20, 0.05), bls_series("APU000074714", 3.30, 0.02),
    bls_series("APU0000703112", 5.60, 0.03), bls_series("APU0000709112", 4.10, 0.02), bls_series("APU0000702111", 1.95, 0.03),
    bls_series("APU0000717311", 7.20, 0.04), bls_series("APU000072610", 0.18, 0.03),
]}})

# FRED
homes = []
q = dt.date(2010, 1, 1)
while q <= TODAY:
    value = 220_000 * (1.045 ** ((q - dt.date(2010, 1, 1)).days / 365.25)) * random.uniform(0.97, 1.03)
    homes.append({"realtime_start": TODAY.isoformat(), "realtime_end": TODAY.isoformat(), "date": q.isoformat(), "value": f"{value:.0f}"})
    q = dt.date(q.year + (q.month + 3 > 12), (q.month + 2) % 12 + 1, 1)
write("fred_MSPUS.json", {"observations": homes})
sp = [{"realtime_start": TODAY.isoformat(), "realtime_end": TODAY.isoformat(), "date": d.isoformat(), "value": f"{2000 * (1.12 ** ((d - (TODAY - dt.timedelta(days=3650))).days / 365.25)) * random.uniform(0.98, 1.02):.2f}"} for d in days(TODAY - dt.timedelta(days=3650), step=3)]
sp.insert(5, {"realtime_start": TODAY.isoformat(), "realtime_end": TODAY.isoformat(), "date": "2017-01-02", "value": "."})
write("fred_SP500.json", {"observations": sp})

# live API
write("live_price.json", {"updated": dt.datetime.now(dt.timezone.utc).isoformat(), "source": {"name": "CoinGecko", "url": "https://www.coingecko.com", "attribution": "Data provided by CoinGecko"},
                          "prices": {"usd": round(prices[-1]["y"], 2), "eur": round(prices[-1]["y"] * 0.89, 2)}, "sats_per": {"usd": round(1e8 / prices[-1]["y"]), "eur": round(1e8 / (prices[-1]["y"] * 0.89))}, "change_24h": {"usd": 1.3, "eur": 2.2}})
write("live_fees.json", {"updated": dt.datetime.now(dt.timezone.utc).isoformat(), "source": {"name": "mempool.space", "url": "https://mempool.space"}, "unit": "sat/vB", "fees": {"fast": 4, "medium": 4, "slow": 3, "economy": 2, "minimum": 1}, "height": 969477, "mempool": {"count": 86126, "vsize_mb": 46.35}})

# World Bank: the page with the workbook link, and a small workbook shaped like the Pink Sheet
(HERE / "worldbank_page.html").write_text('<html><body><a href="https://thedocs.worldbank.org/en/doc/example-0050012026/related/CMO-Historical-Data-Monthly.xlsx">Monthly prices</a></body></html>\n', encoding="utf-8")
import openpyxl  # noqa: E402

book = openpyxl.Workbook()
sheet = book.active
sheet.title = "Monthly Prices"
sheet.append(["World Bank Commodity Price Data (The Pink Sheet)", None, None, None])
sheet.append([None, None, None, None])
sheet.append([None, None, None, None])
sheet.append([None, "Crude oil, average", "Gold", "Silver"])
sheet.append([None, "($/bbl)", "($/troy oz)", "($/troy oz)"])
sheet.append([None, "CRUDE_PETRO", "GOLD", "SILVER"])
m = dt.date(2010, 1, 1)
while m <= TODAY:
    gold = 1100 * (1.055 ** ((m - dt.date(2010, 1, 1)).days / 365.25)) * random.uniform(0.97, 1.03)
    sheet.append([f"{m.year}M{m.month:02d}", 70.0, round(gold, 2), round(gold / 80, 2)])
    m = dt.date(m.year + (m.month == 12), m.month % 12 + 1, 1)
buf = io.BytesIO()
book.save(buf)
(HERE / "worldbank_cmo.xlsx").write_bytes(buf.getvalue())
print("fixtures written to", HERE)
