# Scripts

The Daily Build scripts (step 16 of the Build Recipe) go here: one module per data source (CoinGecko, BLS, FRED, mempool.space, blockchain.com, alternative.me), one per chart (drawn with `lib/chartstyle.py`), and the runner that `.github/workflows/daily-build.yml` calls at 09:00 UTC.
