/**
 * live-data: the Cloudflare Worker behind api.faststatsforsats.com
 *
 * What it does
 *   Every hour (cron "0 * * * *")      pulls the bitcoin price in 30 currencies from CoinGecko and stores it in KV.
 *   Every 10 minutes ("*\/10 * * * *")  pulls fee estimates, the block height, and the mempool size from mempool.space.
 *   On request                          serves the stored JSON with open CORS headers so the three sites (and anyone
 *                                       else) can read it from a browser.
 *
 * Endpoints
 *   GET /price   -> { updated, source, prices: { usd: 0, eur: 0, ... }, sats_per: { usd: 0, ... }, change_24h: { usd: 0, ... } }
 *   GET /fees    -> { updated, source, unit: "sat/vB", fees: { fast, medium, slow, economy, minimum }, height, mempool: { count, vsize_mb } }
 *   GET /status  -> when each feed last updated, the last error if any (never a key)
 *   GET /        -> the list above
 *
 * Settings in the Cloudflare dashboard (Build Recipe, step 15)
 *   KV binding      SATS_DATA      (Workers KV namespace named SATS_DATA)
 *   Secret          COINGECKO_KEY  (CoinGecko Demo key; the Worker still runs without it, within the public limits)
 *   Cron triggers   0 * * * *   and   *\/10 * * * *   (UTC)
 *   Custom domain   api.faststatsforsats.com
 *
 * Budget on the free plan: 24 price writes + 144 fee writes a day, far under KV's 1,000 writes a day;
 * 720 CoinGecko calls a month of the Demo plan's 10,000. The pages fall back to the Daily Build's
 * numbers when this API is unreachable (shared/static/live.js), so a failed run is never visible as a blank.
 */

const CURRENCIES = [
  "usd", "eur", "gbp", "jpy", "cad", "aud", "chf", "cny", "inr", "brl",
  "mxn", "krw", "sgd", "hkd", "nzd", "sek", "nok", "dkk", "pln", "czk",
  "huf", "try", "zar", "aed", "sar", "ils", "thb", "php", "idr", "ars",
];

const SOURCES = {
  price: { name: "CoinGecko", url: "https://www.coingecko.com", attribution: "Data provided by CoinGecko" },
  fees: { name: "mempool.space", url: "https://mempool.space" },
};

const KEYS = { price: "price", fees: "fees", status: "status" };
const PRICE_CRON = "0 * * * *";
const FEES_CRON = "*/10 * * * *";
const USER_AGENT = "faststatsforsats.com live-data worker (contact: jim@faststatsforsats.com)";

export default {
  async scheduled(event, env, ctx) {
    const jobs = [];
    if (event.cron === PRICE_CRON) jobs.push(refreshPrice(env));
    else if (event.cron === FEES_CRON) jobs.push(refreshFees(env));
    else jobs.push(refreshPrice(env), refreshFees(env));      // an unknown or manual trigger refreshes both
    ctx.waitUntil(Promise.allSettled(jobs));
  },

  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";

    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders() });
    if (request.method !== "GET" && request.method !== "HEAD") return json({ error: "GET only" }, 405);

    if (path === "/") {
      return json({
        site: "faststatsforsats.com",
        endpoints: { "/price": "bitcoin price in 30 currencies, hourly", "/fees": "fee estimates, block height, mempool size, every 10 minutes", "/status": "feed health" },
        terms: "Free to use with a link to faststatsforsats.com. Price data: " + SOURCES.price.attribution + ".",
      }, 200, 3600);
    }

    if (path === "/price" || path === "/fees") {
      const key = path.slice(1);
      let stored = await env.SATS_DATA.get(key);
      if (!stored) {
        // Cold start: nothing in KV yet (first deploy, or the namespace was recreated). Fill it on demand.
        const fresh = key === "price" ? await refreshPrice(env) : await refreshFees(env);
        if (fresh) stored = JSON.stringify(fresh);
      }
      if (!stored) return json({ error: "no data yet; try again in a few minutes" }, 503, 0);
      return new Response(stored, { status: 200, headers: { ...corsHeaders(), ...jsonHeaders(key === "price" ? 300 : 60) } });
    }

    if (path === "/status") {
      const [price, fees, status] = await Promise.all([
        env.SATS_DATA.get(KEYS.price, "json"),
        env.SATS_DATA.get(KEYS.fees, "json"),
        env.SATS_DATA.get(KEYS.status, "json"),
      ]);
      return json({
        now: new Date().toISOString(),
        price_updated: price ? price.updated : null,
        fees_updated: fees ? fees.updated : null,
        last_error: status ? status.last_error : null,
        last_error_at: status ? status.last_error_at : null,
        has_coingecko_key: Boolean(env.COINGECKO_KEY),
      }, 200, 0);
    }

    return json({ error: "not found", endpoints: ["/price", "/fees", "/status"] }, 404, 0);
  },
};

/* ---------- the two feeds ---------- */

async function refreshPrice(env) {
  try {
    const params = new URLSearchParams({
      ids: "bitcoin",
      vs_currencies: CURRENCIES.join(","),
      include_24hr_change: "true",
      include_last_updated_at: "true",
      precision: "full",
    });
    const headers = { accept: "application/json", "user-agent": USER_AGENT };
    if (env.COINGECKO_KEY) headers["x-cg-demo-api-key"] = env.COINGECKO_KEY;
    const res = await fetch("https://api.coingecko.com/api/v3/simple/price?" + params, { headers });
    if (!res.ok) throw new Error("CoinGecko answered " + res.status);
    const body = await res.json();
    const btc = body.bitcoin;
    if (!btc || typeof btc.usd !== "number") throw new Error("CoinGecko answer had no bitcoin.usd");

    const prices = {}, change = {}, satsPer = {};
    for (const c of CURRENCIES) {
      if (typeof btc[c] !== "number") continue;
      prices[c] = btc[c];
      satsPer[c] = Math.round(100_000_000 / btc[c]);           // sats one unit of the currency buys
      const ch = btc[c + "_24h_change"];
      if (typeof ch === "number") change[c] = Math.round(ch * 100) / 100;
    }
    const payload = {
      updated: new Date().toISOString(),
      source_updated: btc.last_updated_at ? new Date(btc.last_updated_at * 1000).toISOString() : null,
      source: SOURCES.price,
      prices,
      sats_per: satsPer,
      change_24h: change,
    };
    await env.SATS_DATA.put(KEYS.price, JSON.stringify(payload));
    return payload;
  } catch (err) {
    await recordError(env, "price", err);
    return null;
  }
}

async function refreshFees(env) {
  try {
    const headers = { accept: "application/json", "user-agent": USER_AGENT };
    const [feesRes, heightRes, mempoolRes] = await Promise.all([
      fetch("https://mempool.space/api/v1/fees/recommended", { headers }),
      fetch("https://mempool.space/api/blocks/tip/height", { headers }),
      fetch("https://mempool.space/api/mempool", { headers }),
    ]);
    if (!feesRes.ok) throw new Error("mempool.space fees answered " + feesRes.status);
    const f = await feesRes.json();
    const height = heightRes.ok ? Number(await heightRes.text()) : null;
    const mem = mempoolRes.ok ? await mempoolRes.json() : null;

    const payload = {
      updated: new Date().toISOString(),
      source: SOURCES.fees,
      unit: "sat/vB",
      fees: {
        fast: f.fastestFee,        // next block
        medium: f.halfHourFee,     // about 30 minutes
        slow: f.hourFee,           // about an hour
        economy: f.economyFee,
        minimum: f.minimumFee,
      },
      height: Number.isFinite(height) ? height : null,
      mempool: mem ? { count: mem.count, vsize_mb: Math.round((mem.vsize / 1_000_000) * 100) / 100 } : null,
    };
    await env.SATS_DATA.put(KEYS.fees, JSON.stringify(payload));
    return payload;
  } catch (err) {
    await recordError(env, "fees", err);
    return null;
  }
}

async function recordError(env, feed, err) {
  try {
    await env.SATS_DATA.put(KEYS.status, JSON.stringify({
      last_error: feed + ": " + (err && err.message ? err.message : String(err)),
      last_error_at: new Date().toISOString(),
    }));
  } catch (_) {
    // KV itself failing: nothing more to do; the next cron tries again
  }
}

/* ---------- response helpers ---------- */

function corsHeaders() {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET, HEAD, OPTIONS",
    "access-control-allow-headers": "content-type",
    "access-control-max-age": "86400",
  };
}

function jsonHeaders(maxAge) {
  return {
    "content-type": "application/json; charset=utf-8",
    "cache-control": maxAge > 0 ? "public, max-age=" + maxAge : "no-store",
    "x-content-type-options": "nosniff",
  };
}

function json(body, status = 200, maxAge = 0) {
  return new Response(JSON.stringify(body, null, 2), { status, headers: { ...corsHeaders(), ...jsonHeaders(maxAge) } });
}