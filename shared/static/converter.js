/* The sats converter (/tools/sats-converter/).
   Starts from the prices the Daily Build baked into the page (data-prices), then refreshes them from the
   live API through live.js (which fires a "sats:price" event when its fetch succeeds). */
(function () {
  var form = document.getElementById("converter");
  if (!form) return;
  var prices = {};
  try { prices = JSON.parse(form.getAttribute("data-prices") || "{}"); } catch (e) { prices = {}; }

  var amountIn = document.getElementById("conv-amount");
  var currency = document.getElementById("conv-currency");
  var satsOut = document.getElementById("conv-sats");
  var btcOut = document.getElementById("conv-btc");
  var satsIn = document.getElementById("conv-sats-in");
  var moneyOut = document.getElementById("conv-money");
  var priceOut = document.getElementById("conv-price");

  var SYMBOL = { usd: "$", eur: "€", gbp: "£", cad: "C$", aud: "A$", jpy: "¥", inr: "₹", chf: "CHF ", brl: "R$", mxn: "MX$" };
  function fmt(n, digits) { return Number(n).toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits }); }
  function money(n, cur) { var sym = SYMBOL[cur] || (cur.toUpperCase() + " "); return sym + fmt(n, n >= 1000 ? 0 : 2); }
  function sats(n) { if (n >= 100) return fmt(n, 0) + " sats"; if (n >= 10) return fmt(n, 1) + " sats"; return fmt(n, 2) + " sats"; }

  function update() {
    var cur = currency.value;
    var p = prices[cur];
    if (!p) { satsOut.textContent = "Price unavailable"; btcOut.textContent = ""; return; }
    var amount = parseFloat(amountIn.value);
    if (isNaN(amount) || amount < 0) amount = 0;
    var btc = amount / p;
    satsOut.textContent = sats(btc * 100000000);
    btcOut.textContent = fmt(btc, btc >= 1 ? 4 : 8) + " BTC";
    priceOut.textContent = money(p, cur) + " per bitcoin";
    var s = parseFloat(satsIn.value);
    moneyOut.textContent = (isNaN(s) || s < 0) ? "" : "= " + money(s / 100000000 * p, cur);
  }

  amountIn.addEventListener("input", update);
  currency.addEventListener("change", update);
  satsIn.addEventListener("input", update);
  document.addEventListener("sats:price", function (ev) {
    if (ev.detail && ev.detail.prices) { prices = ev.detail.prices; update(); }
  });
  update();
})();
