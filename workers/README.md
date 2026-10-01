# Workers

The live-data Worker (step 15 of the Build Recipe) goes here as `live-data.js`, with its KV binding `SATS_DATA`, the `COINGECKO_KEY` secret, and two cron triggers: `0 * * * *` for price and `*/10 * * * *` for fees. It answers `/price` and `/fees` at api.faststatsforsats.com in the shape described in `data/README.md`.
