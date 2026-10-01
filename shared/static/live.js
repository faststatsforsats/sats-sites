/* Live figures.
   A page marks a number like this:
     <span class="live" data-live="price" data-currency="usd">$0</span>
     <span class="live-when" data-live-when="price"></span>
   The script asks the Worker (api.faststatsforsats.com, step 15) for the latest value and swaps it in.
   If the API is unreachable or over its daily limit, the text the Daily Build baked into the page stays.
   Keys: price (data-currency: usd, eur, ...), sats-per-dollar, fees (data-tier: fast, medium, slow). */
(function () {
  var body = document.body;
  var api = body.getAttribute("data-api");
  var nodes = document.querySelectorAll("[data-live]");
  if (!api || !nodes.length || !window.fetch) return;

  function fmt(n, digits) {
    return Number(n).toLocaleString(undefined, { maximumFractionDigits: digits === undefined ? 0 : digits });
  }

  function stamp(key, when) {
    var marks = document.querySelectorAll('[data-live-when="' + key + '"]');
    if (!when) return;
    var d = new Date(when);
    for (var i = 0; i < marks.length; i++) {
      marks[i].textContent = "as of " + d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
    }
  }

  var needPrice = false, needFees = false;
  for (var i = 0; i < nodes.length; i++) {
    var k = nodes[i].getAttribute("data-live");
    if (k === "price" || k === "sats-per-dollar") needPrice = true;
    if (k === "fees") needFees = true;
  }

  if (needPrice) {
    fetch(api + "/price", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (data) {
      if (!data || !data.prices) return;
      for (var i = 0; i < nodes.length; i++) {
        var el = nodes[i], key = el.getAttribute("data-live");
        if (key === "price") {
          var cur = (el.getAttribute("data-currency") || "usd").toLowerCase();
          if (data.prices[cur] !== undefined) {
            el.textContent = (cur === "usd" ? "$" : "") + fmt(data.prices[cur], data.prices[cur] < 10 ? 2 : 0) + (cur === "usd" ? "" : " " + cur.toUpperCase());
          }
        } else if (key === "sats-per-dollar" && data.prices.usd) {
          el.textContent = fmt(100000000 / data.prices.usd) + " sats";
        }
      }
      stamp("price", data.updated);
    }).catch(function () {});
  }

  if (needFees) {
    fetch(api + "/fees", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (data) {
      if (!data || !data.fees) return;
      for (var i = 0; i < nodes.length; i++) {
        var el = nodes[i];
        if (el.getAttribute("data-live") !== "fees") continue;
        var tier = el.getAttribute("data-tier") || "medium";
        if (data.fees[tier] !== undefined) el.textContent = fmt(data.fees[tier]) + " sat/vB";
      }
      stamp("fees", data.updated);
    }).catch(function () {});
  }
})();
