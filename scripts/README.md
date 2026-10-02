# Scripts: the Daily Build

`.github/workflows/daily-build.yml` runs `scripts/daily_build.py` every morning at 09:00 UTC and commits what it produces. The commit lands in `data/`, `charts/`, and `content/stats/charts/`, which rebuilds the Stats site on Cloudflare Pages. Nothing here is run by hand on a normal day.

| File | What it does |
| --- | --- |
| `daily_build.py` | The runner: pull the sources, write `data/*.json`, draw the charts, refresh the chart pages, write `charts/index.json` and `data/latest.json`, print a summary |
| `chartbook.py` | One function per chart, all drawn through `lib/chartstyle.py`. Add a chart here |
| `pages.py` | The programmatic chart pages under `content/stats/charts/`. The build owns the `chart` and `updated` front matter and the text between `<!-- auto:start -->` and `<!-- auto:end -->`; the explainer the Content Writer adds below the markers is kept |
| `series.py` | Date-series helpers: monthly and quarterly averages, "a year ago" lookups, sats-per-unit conversions |
| `nostr_post.py` | Posts the chart of the day as the site's Nostr account (NIP-01 note, BIP-340 signature via coincurve). Rotates through the charts by day of the year |
| `sources/` | One module per source; each returns plain `(date, value)` lists and raises `SourceError` when the source is down |
| `fixtures/` | Synthetic data shaped like each source, for offline runs: `python3 scripts/daily_build.py --fixtures`. Regenerate with `python3 scripts/fixtures/generate.py` |

## Sources and keys

| Source | What | Key | Module |
| --- | --- | --- | --- |
| blockchain.com charts | daily price (USD) and hash rate since 2009 | none | `sources/blockchain_com.py` |
| alternative.me | Crypto Fear & Greed Index, daily since 2018 | none | `sources/alternative_me.py` |
| U.S. Bureau of Labor Statistics API v2 | CPI and 25 average prices (eggs, gasoline, milk, bread, coffee, beer, diesel, and more; the list is `SERIES` in the module), monthly, fetched in batches of 50 | `BLS_KEY` | `sources/bls.py` |
| FRED | median new-home price (MSPUS, quarterly), S&P 500 (daily, last 10 years) | `FRED_KEY` | `sources/fred.py` |
| World Bank Pink Sheet | gold, USD per troy ounce, monthly since 1960 (FRED removed the daily LBMA gold series in 2022) | none | `sources/worldbank.py` |
| api.faststatsforsats.com | today's price in 30 currencies (CoinGecko, via the Worker) and the fee tiers | none | `sources/live_api.py` |

Keys live in the repository's secrets store (Settings, Secrets and variables, Actions): `BLS_KEY` and `FRED_KEY` for the data, `NOSTR_NSEC` for the daily post. The post is skipped, without failing the build, until `NOSTR_NSEC` exists; add it at launch (step 35), once the custom domains are live, so the first note does not carry dead links.

## When a source fails

The runner keeps yesterday's data file for that source, draws what it can, and prints `FAIL <source>: <reason>` in the workflow log. The job still succeeds as long as at least one chart was drawn. A source that fails three days running is worth a look: open the Actions tab, the latest Daily Build run, and read the "Pull data" step.

## Running it yourself

```
python3 -m pip install -r requirements-daily.txt
python3 scripts/daily_build.py --fixtures      # offline, synthetic data
python3 scripts/daily_build.py --offline       # redraw the charts from the saved data/ files (no sources touched; latest.json left alone)
BLS_KEY=... FRED_KEY=... python3 scripts/daily_build.py   # the real thing
python3 scripts/nostr_post.py --dry-run         # print today's note without posting
python3 scripts/nostr_post.py --self-test       # key handling and signing checks
```

## The charts (October 2026)

sats-per-dollar, price-usd, eggs-in-sats, gold-in-sats, home-in-bitcoin, fear-greed, hashrate, twenty-five-a-week (the sats a $25 buy every Monday since January 2020 added up to; the October campaign's hook chart, also shown on the Acts page /first-100k-sats/). Each writes a light PNG, a dark PNG, and an SVG into `charts/`, an entry in `charts/index.json`, and a page at `/charts/<slug>/` on the Stats site.

`scripts/checklist_pdf.py` is separate from the Daily Build: it draws the one-page Sats Stacker's Starter Checklist into `sites/acts/static/` from the words in `scripts/checklist.yml` (edit the words there, then run it by hand; it needs `reportlab`, `pyyaml`, and `pillow`, and it picks the largest type that keeps everything on one page).

The look (lib/chartstyle.py): the key figure in the title is set in the series color; the line is 3 px with a soft halo and a wash fading beneath it; the latest value sits in a bold pill at the line's end; the all-time low and the high of the last five years (or the all-time high, the record, the greediest and most fearful days) are marked with a dot and a two-line tag; the halvings are thin vertical lines on the price, sats-per-dollar, and hash rate charts; the Stats coin sits in the footer corner. Tags are placed by scoring each candidate spot against the line, the other tags, and the figure's edges (`SATS_LABEL_DEBUG=1` prints the scores). The SVG keeps only the line (no halo or wash) so it stays small.
