/* Fast Stats for Sats: the sats badge.  https://faststatsforsats.com/tools/embed/

   Paste this where the badge should appear:

     <a class="sats-badge" href="https://faststatsforsats.com/tools/sats-converter/" data-amount="25" data-currency="usd">$25 in sats</a>
     <script async src="https://faststatsforsats.com/embed.js"></script>

   data-amount    the price to show
   data-currency  its currency code (usd, eur, gbp, and 27 more; the embed page lists them)
   data-label     optional: a name to put in front of the amount, such as "Flat white"

   What it does: turns each such link into a small badge that shows the amount in sats, worked out from a bitcoin
   price that is checked hourly, with the time of that price and the credits.
   What it does not do: it sets no cookies, stores nothing in the browser, and reads nothing from the page it sits on.
   It asks api.faststatsforsats.com for the price and loads one small image. If the price cannot be reached, or the
   amount or currency is not one it knows, the link stays a plain link.
   Free to use as long as the credits stay in place: https://faststatsforsats.com/terms/ */
(function () {
  "use strict";
  // Pasted more than once on a page: the first copy does the work, the others only ask it to look again.
  if (window.SatsBadge) { window.SatsBadge.render(); return; }

  var SITE = "https://faststatsforsats.com";
  var API = "https://api.faststatsforsats.com/price";
  var SYMBOL = { usd: "$", eur: "€", gbp: "£", cad: "C$", aud: "A$", jpy: "¥", inr: "₹", chf: "CHF ", brl: "R$", mxn: "MX$" };

  // The badge draws inside its own shadow tree, so the page's styles do not reach in and these do not leak out.
  var STYLE = "<style>" +
    ":host{all:initial;direction:ltr;unicode-bidi:isolate;display:inline-block;max-width:100%;vertical-align:middle}" +   // "all" leaves direction alone
    ".b{display:inline-flex;align-items:center;gap:10px;box-sizing:border-box;max-width:100%;padding:10px 14px;border-radius:10px;" +
    "background:#071829;color:#a9b6c8;font:14px/1.4 system-ui,-apple-system,'Segoe UI',sans-serif;text-align:left}" +
    ".c{width:30px;height:30px;flex:none}" +
    ".t{display:block;min-width:0}" +
    ".f{display:block;color:#fff;font-size:18px;font-weight:700;line-height:1.25;text-decoration:none}" +
    ".f:hover{text-decoration:underline}" +
    ".n{color:#f97e1b}" +
    ".w,.s{display:block}" +
    ".s a{color:#d6deea}" +
    "a:focus-visible{outline:2px solid #5cc3ff;outline-offset:2px}" +
    "</style>";
  // Fixed markup only; every figure and label is put in as text below, never as markup.
  var BODY = '<span class="b"><img class="c" alt="" width="30" height="30" src="' + SITE + '/static/brand/stats-coin.png">' +
    '<span class="t"><a class="f" target="_blank" rel="noopener" title="Sats means satoshis, the smallest unit of bitcoin.">' +
    '<span class="a"></span><span class="n"></span></a>' +
    '<span class="w"></span>' +
    '<span class="s"><a target="_blank" rel="noopener" href="' + SITE + '/">Fast Stats for Sats</a> · Data provided by ' +
    '<a target="_blank" rel="noopener" href="https://www.coingecko.com">CoinGecko</a></span></span></span>';

  var price = null;       // the API's answer, once it has arrived
  var waiting = false;    // a request is out, or one failed less than a minute ago

  function fmt(n, digits) {
    return Number(n).toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits });
  }
  function money(n, cur) {
    return (SYMBOL[cur] || (cur.toUpperCase() + " ")) + fmt(n, n % 1 === 0 ? 0 : 2);
  }
  function sats(n) {
    if (n >= 100) return fmt(n, 0) + " sats";
    if (n >= 10) return fmt(n, 1) + " sats";
    return fmt(n, 2) + " sats";
  }

  function draw(link) {
    var amount = parseFloat(link.getAttribute("data-amount"));
    var cur = (link.getAttribute("data-currency") || "usd").toLowerCase();
    var p = price.prices[cur];
    if (!(amount > 0) || !isFinite(amount) || !p || !link.parentNode) return;    // leave the plain link as it is
    var label = (link.getAttribute("data-label") || "").replace(/^\s+|\s+$/g, "").slice(0, 60);
    // an element of its own name, so a page's rules for span or div do not land on the badge
    var host = document.createElement("sats-badge");
    if (!host.attachShadow) return;
    var root = host.attachShadow({ mode: "open" });
    root.innerHTML = STYLE + BODY;
    var figure = root.querySelector(".f");
    // the figure links to this site only: the address the link was given if it is one of ours, otherwise the converter
    figure.href = link.href.indexOf(SITE + "/") === 0 ? link.href : SITE + "/tools/sats-converter/";
    root.querySelector(".a").textContent = (label ? label + ": " : "") + money(amount, cur) + " = ";
    root.querySelector(".n").textContent = sats(amount / p * 100000000);
    var when = price.updated ? new Date(price.updated) : null;
    root.querySelector(".w").textContent = when && !isNaN(when) ? "as of " + when.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }) : "";
    link.parentNode.replaceChild(host, link);
  }

  function render() {
    var links = document.querySelectorAll("a.sats-badge[data-amount]");
    if (!links.length) return;
    if (price) {
      for (var i = 0; i < links.length; i++) draw(links[i]);
      return;
    }
    if (waiting || !window.fetch) return;
    waiting = true;
    fetch(API, { credentials: "omit", referrerPolicy: "no-referrer" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (data && data.prices) { price = data; waiting = false; render(); }
        else setTimeout(function () { waiting = false; }, 60000);
      })
      .catch(function () { setTimeout(function () { waiting = false; }, 60000); });
  }

  // A page that adds a badge link later (the embed page's form does) calls SatsBadge.render() to draw it.
  window.SatsBadge = { render: render };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", render);
  render();
})();
