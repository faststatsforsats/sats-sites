# Data

The Daily Build (`scripts/daily_build.py`, run by `.github/workflows/daily-build.yml` every morning at 09:00 UTC) writes these files and commits them. The Stats site publishes the folder as https://faststatsforsats.com/data/ with open CORS headers, so anyone can fetch the numbers. Nothing in here is typed by hand.

Every series file has the same shape:

```
{"updated": "2026-10-02T09:01:00+00:00",
 "source": {"name": "...", "url": "..."},
 "series": {"name": "...", "unit": "...", "frequency": "daily|monthly|quarterly", "points": [["2026-10-01", 84908.43], ...]}}
```

| File | Source | Contents |
| --- | --- | --- |
| `latest.json` | all of the below | The headline figures: today's price in 30 currencies and sats per unit (from the live API), the daily average price, fee tiers and block height, the Fear and Greed reading, the latest CPI, and each chart's latest value and finding |
| `price-daily.json` | blockchain.com | Daily average price in USD since 2010 |
| `network.json` | blockchain.com | Estimated hash rate, TH/s, daily since 2010 |
| `fear-greed.json` | alternative.me | Daily index with its label, since 2018 (points are `[date, value, label]`) |
| `cpi.json` | BLS (CUUR0000SA0) | CPI-U all items, monthly |
| `eggs.json`, `gasoline.json`, `ground_beef.json`, `milk.json`, `bread.json`, `coffee.json`, `electricity.json`, and one file per item in `scripts/sources/bls.py` SERIES (bananas, chicken, bacon, flour, rice, sugar, butter, potatoes, tomatoes, oranges, apples, wheat_bread, diesel, premium_gas, natural_gas, fuel_oil, beer, wine) | BLS average prices | USD per unit, monthly, U.S. city average. Each file carries `bls_series_id`; the Stats site builds `/items/<slug>/` from every file that has one. |
| `homes.json` | FRED (MSPUS) | Median sales price of new houses sold, quarterly |
| `sp500.json` | FRED (SP500) | S&P 500 daily close, last 10 years |
| `gold.json` | World Bank Pink Sheet | Gold, USD per troy ounce, monthly average |

Source terms to keep: "Data provided by CoinGecko" beside CoinGecko figures; the FRED and BLS sentences from the style guide on pages that use those series; the World Bank line for gold. `lib/site.py` adds them when a page lists the source in its `attribution` front matter.
