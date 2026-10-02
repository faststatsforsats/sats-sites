/* Live figures.
   A page marks a number like this:
     <span class="live" data-live="price" data-currency="usd">$0</span>
     <span class="live-when" data-live-when="price"></span>
   The script asks the Worker (api.faststatsforsats.com, step 15) for the latest value and swaps it in.
   If the API is unreachable or over its daily limit, the text the Daily Build baked into the page stays.
   Keys:
     price            data-currency (usd, eur, ...)
     sats-per-dollar
     sats-for         data-amount and data-currency: how many sats that amount buys
     money-for        data-sats and data-currency: what that many sats are worth
     change           data-currency: 24-hour change in percent
     fees             data-tier: fast, medium, slow
     height           the latest block height
     to-halving       blocks left until the next halving (from the height)
     supply           bitcoin issued so far, in millions (from the height)
   An element with data-live-want="price" asks for the price fetch (and the "sats:price" event) without showing a number. */
(function () {
  var body = document.body;
  var api = body.getAttribute("data-api");
  var nodes = document.querySelectorAll("[data-live]");
  // A page with no live numbers of its own can still ask for the price event (the converter does)
  var wantsPrice = document.querySelector("[data-live-want~='price']");
  if (!api || (!nodes.length && !wantsPrice) || !window.fetch) return;

  var SYMBOL = { usd: "$", eur: "€", gbp: "£", cad: "C$", aud: "A$", jpy: "¥", inr: "₹", chf: "CHF ", brl: "R$", mxn: "MX$" };

  function fmt(n, digits) {
    return Number(n).toLocaleString(undefined, { maximumFractionDigits: digits === undefined ? 0 : digits, minimumFractionDigits: digits === undefined ? 0 : digits });
  }
  function money(n, cur) {
    var sym = SYMBOL[cur] || (cur.toUpperCase() + " ");
    return sym + fmt(n, n >= 1000 ? 0 : 2);
  }
  function sats(n) {
    if (n >= 100) return fmt(n) + " sats";
    if (n >= 10) return fmt(n, 1) + " sats";
    return fmt(n, 2) + " sats";
  }
  function minedSupply(height) {
    // bitcoin issued by the block subsidy through this height (block 0 included)
    var total = 0, subsidy = 50, blocks = height + 1;
    while (blocks > 0) { var n = Math.min(blocks, 210000); total += n * subsidy; blocks -= n; subsidy /= 2; }
    return total;
  }
  function stamp(key, when) {
    var marks = document.querySelectorAll('[data-live-when="' + key + '"]');
    if (!when) return;
    var d = new Date(when);
    for (var i = 0; i < marks.length; i++) {
      marks[i].textContent = "as of " + d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
    }
  }

  var needPrice = !!wantsPrice, needFees = false;
  for (var i = 0; i < nodes.length; i++) {
    var k = nodes[i].getAttribute("data-live");
    if (k === "price" || k === "sats-per-dollar" || k === "sats-for" || k === "money-for" || k === "change") needPrice = true;
    if (k === "fees" || k === "height" || k === "to-halving" || k === "supply") needFees = true;
  }

  if (needPrice) {
    fetch(api + "/price", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (data) {
      if (!data || !data.prices) return;
      for (var i = 0; i < nodes.length; i++) {
        var el = nodes[i], key = el.getAttribute("data-live");
        var cur = (el.getAttribute("data-currency") || "usd").toLowerCase();
        var p = data.prices[cur];
        if (key === "price" && p !== undefined) {
          el.textContent = money(p, cur);
        } else if (key === "sats-per-dollar" && data.prices.usd) {
          el.textContent = fmt(100000000 / data.prices.usd) + " sats";
        } else if (key === "sats-for" && p) {
          var amount = parseFloat(el.getAttribute("data-amount") || "0");
          el.textContent = sats(amount / p * 100000000);
        } else if (key === "money-for" && p) {
          var n = parseFloat(el.getAttribute("data-sats") || "0");
          el.textContent = money(n / 100000000 * p, cur);
        } else if (key === "change" && data.change_24h && data.change_24h[cur] !== undefined) {
          var c = data.change_24h[cur];
          el.textContent = (c >= 0 ? "+" : "") + fmt(c, 1) + "%";
        }
      }
      stamp("price", data.updated);
      document.dispatchEvent(new CustomEvent("sats:price", { detail: data }));
    }).catch(function () {});
  }

  if (needFees) {
    fetch(api + "/fees", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (data) {
      if (!data || !data.fees) return;
      for (var i = 0; i < nodes.length; i++) {
        var el = nodes[i], key = el.getAttribute("data-live");
        if (key === "height" && data.height) { el.textContent = fmt(data.height); continue; }
        if (key === "to-halving" && data.height) { el.textContent = fmt((Math.floor(data.height / 210000) + 1) * 210000 - data.height); continue; }
        if (key === "supply" && data.height) { el.textContent = fmt(minedSupply(data.height) / 1000000, 2) + " million"; continue; }
        if (key !== "fees") continue;
        var tier = el.getAttribute("data-tier") || "medium";
        if (data.fees[tier] !== undefined) el.textContent = fmt(data.fees[tier]) + " sat/vB";
      }
      stamp("fees", data.updated);
    }).catch(function () {});
  }
})();
