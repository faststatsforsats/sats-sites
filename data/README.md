# Data

The Daily Build (step 16, `.github/workflows/daily-build.yml`) writes these files every morning at 09:00 UTC and commits them. The Stats site publishes the folder as https://faststatsforsats.com/data/ with open CORS headers, so anyone can fetch the numbers. Nothing in here is typed by hand.

| File | Written by | Contents |
| --- | --- | --- |
| `latest.json` | the Daily Build | One object with today's headline figures: price in the main currencies, sats per dollar, the fee tiers, the Fear and Greed value, the latest CPI figure, plus the pull time and source for each |
| `price-daily.json` | the Daily Build (CoinGecko) | Daily closing price in USD since 2011, one row per day |
| `cpi.json` | the Daily Build (BLS) | CPI-U, all items, monthly, with the BLS series id |
| `eggs.json` | the Daily Build (BLS) | Average price of a dozen grade A large eggs, monthly, US city average |
| `gold.json` | the Daily Build (FRED) | Gold price series used for the bitcoin-versus-gold chart |
| `fear-greed.json` | the Daily Build (alternative.me) | Daily Fear and Greed index |
| `network.json` | the Daily Build (blockchain.com, mempool.space) | Hashrate, difficulty, and fee history |

Every file carries `updated` (ISO 8601, UTC) and `source` (name and URL). The live Worker (step 15) answers the same shape for `/price` and `/fees`, which is what `shared/static/live.js` reads.

Source terms to keep: "Data provided by CoinGecko" beside CoinGecko figures; the FRED and BLS sentences from the style guide on pages that use those series. `lib/site.py` adds them when a page lists the source in its `attribution` front matter.
