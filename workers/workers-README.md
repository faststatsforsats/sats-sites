# Workers

## live-data (api.faststatsforsats.com)

`live-data.js` is the Worker that keeps the live numbers fresh so the sites never make a reader wait on a third-party API. Every hour it stores the bitcoin price in 30 currencies (CoinGecko), and every 10 minutes it stores fee estimates, the block height, and the mempool size (mempool.space), all in a Workers KV namespace. Requests read from KV, so the Worker answers in a few milliseconds and the sources see one call an hour, not one per visitor.

| Endpoint | Refresh | Shape |
| --- | --- | --- |
| `/price` | hourly | `updated`, `source`, `prices` (one number per currency code), `sats_per` (sats one unit buys), `change_24h` (percent) |
| `/fees` | every 10 minutes | `updated`, `source`, `unit` (sat/vB), `fees` (`fast`, `medium`, `slow`, `economy`, `minimum`), `height`, `mempool` (`count`, `vsize_mb`) |
| `/status` | live | when each feed last updated, the last error if any |
| `/` | | the list above |

Every response carries `Access-Control-Allow-Origin: *`, so `shared/static/live.js` on the three sites can read it from the browser. If KV is empty (first deploy), `/price` and `/fees` fill it on demand.

### Deploying it (Build Recipe, step 15)

1. Workers KV, Create instance, name `SATS_DATA`.
2. Workers & Pages, Create, Workers tab, start from the Hello World template, name `live-data`, Deploy. Then Edit code, replace everything with `live-data.js`, Save and deploy.
3. Bindings: add a KV namespace binding, variable name `SATS_DATA`, pick the `SATS_DATA` namespace.
4. Settings, Variables and Secrets: add a Secret named `COINGECKO_KEY` with the Demo key from step 9. The Worker also runs without it, within CoinGecko's public limits, so this can be added later.
5. Settings, Triggers, Cron Triggers: `0 * * * *` and `*/10 * * * *` (UTC).
6. Settings, Domains & Routes, Add, Custom Domain: `api.faststatsforsats.com`.
7. Test: `https://api.faststatsforsats.com/price` and `/fees` return JSON with an `updated` time from the last hour; `/status` shows no error.

### Changing it

Edit `workers/live-data.js` in this repository first, then paste the new file into the Worker's editor and Save and deploy, so the repository always holds the code that is running. Adding a currency means adding its code to the `CURRENCIES` list; CoinGecko's `/simple/supported_vs_currencies` lists what it accepts.

### Limits that matter

Free plan: 100,000 requests a day and 10 ms of CPU per request for the Worker; 100,000 reads and 1,000 writes a day for KV. This Worker writes 168 times a day. If the sites ever pass 100,000 API hits a day, the pages fall back to the Daily Build's figures, which `live.js` already handles.
