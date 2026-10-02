/* Embed code on the site's own pages: the copy buttons, and the badge form on the embed page.

   Copy buttons: a button with data-copy="some-id" copies the text of the element with that id. The page writes the
   button hidden and this script shows it, so a reader without scripts sees the code and no dead button.

   The badge form (#badge-form, shared/templates/_embed_badge.html) rewrites the badge and its code as the amount,
   currency, or label changes. It starts from ?amount=, ?currency=, and ?label= when the address carries them, so a
   link can open the page on someone's own price:  /tools/embed/?amount=4.5&currency=usd&label=Flat%20white
   The badge itself is drawn by the public script (sites/stats/static/embed.js), the same one another site loads. */
(function () {
  function wire(button) {
    button.hidden = false;
    button.addEventListener("click", function () {
      var code = document.getElementById(button.getAttribute("data-copy"));
      if (!code) return;
      var done = button.parentNode.querySelector(".copy-done");
      function copied() {
        if (!done) return;
        done.textContent = "Copied";
        setTimeout(function () { done.textContent = ""; }, 2500);
      }
      function select() {
        // no clipboard access (an old browser, or a page not served over https): select the code so Ctrl+C takes it
        var range = document.createRange();
        range.selectNodeContents(code);
        var selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(code.textContent).then(copied, select);
      else select();
    });
  }
  var buttons = document.querySelectorAll("button[data-copy]");
  for (var i = 0; i < buttons.length; i++) wire(buttons[i]);

  var form = document.getElementById("badge-form");
  if (!form) return;
  var site = form.getAttribute("data-stats-url");
  var amountIn = document.getElementById("badge-amount");
  var currency = document.getElementById("badge-currency");
  var labelIn = document.getElementById("badge-label");
  var preview = document.getElementById("badge-preview");
  var code = document.getElementById("badge-code");
  if (!site || !amountIn || !currency || !labelIn || !preview || !code) return;

  var SYMBOL = { usd: "$", eur: "€", gbp: "£", cad: "C$", aud: "A$", jpy: "¥", inr: "₹", chf: "CHF ", brl: "R$", mxn: "MX$" };
  // The words inside the link are what a reader sees if the badge cannot be drawn. They are written into the code
  // once, so they use one fixed number style and do not depend on who made the code.
  function money(n, cur) {
    var digits = n % 1 === 0 ? 0 : 2;
    return (SYMBOL[cur] || (cur.toUpperCase() + " ")) + Number(n).toLocaleString("en-US", { maximumFractionDigits: digits, minimumFractionDigits: digits });
  }
  function esc(text) {
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function update() {
    var amount = parseFloat(amountIn.value);
    if (!(amount > 0) || !isFinite(amount)) return;      // nothing to show yet: keep the last badge and code
    var cur = currency.value;
    var label = labelIn.value.replace(/^\s+|\s+$/g, "");
    var text = (label ? label + ": " : "") + money(amount, cur) + " in sats";
    var address = site + "/tools/sats-converter/";

    code.textContent = '<a class="sats-badge" href="' + address + '" data-amount="' + amount + '" data-currency="' + cur + '"' +
      (label ? ' data-label="' + esc(label) + '"' : "") + ">" + esc(text) + "</a>\n" +
      '<script async src="' + site + '/embed.js"></' + "script>";

    // The preview: take out the old badge (or its plain link), leave the script tag where it is, and put in a
    // fresh link for the badge script to draw.
    var marker = null;
    for (var i = preview.childNodes.length - 1; i >= 0; i--) {
      var node = preview.childNodes[i];
      if (node.nodeType === 1 && node.tagName === "SCRIPT") marker = node;
      else preview.removeChild(node);
    }
    var link = document.createElement("a");
    link.className = "sats-badge";
    link.href = address;
    link.setAttribute("data-amount", String(amount));
    link.setAttribute("data-currency", cur);
    if (label) link.setAttribute("data-label", label);
    link.textContent = text;
    preview.insertBefore(link, marker);
    if (window.SatsBadge) window.SatsBadge.render();
  }

  amountIn.addEventListener("input", update);
  currency.addEventListener("change", update);
  labelIn.addEventListener("input", update);

  // Start from the address, when it names a price
  var changed = false;
  try {
    var query = new URLSearchParams(window.location.search);
    var a = parseFloat(query.get("amount"));
    if (a > 0 && isFinite(a)) { amountIn.value = String(a); changed = true; }
    var c = (query.get("currency") || "").toLowerCase().replace(/[^a-z]/g, "");
    if (c && currency.querySelector('option[value="' + c + '"]')) { currency.value = c; changed = true; }
    var l = (query.get("label") || "").slice(0, 40);
    if (l) { labelIn.value = l; changed = true; }
  } catch (e) { /* an old browser: the form starts from its own values */ }
  if (changed) update();
})();
