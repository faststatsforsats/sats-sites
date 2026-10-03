/* Small actions on a page: send it to a friend, the knowledge check, and ticking off the twelve acts.

   Nothing here talks to a server, and nothing asks what a reader holds.

   Send to a friend: a link with data-share opens the device's own share sheet where there is one; otherwise it copies
   the page's address and says so; if neither works it is a plain mailto: link, as it is with no script.

   Knowledge check (shared/templates/route.html): the button marks each question and gives a score. After a wrong pick
   the right option is named. The picks are never stored. With no script each answer sits behind "Show the answer".

   Twelve acts (shared/templates/campaign.html, home_acts.html): a tick box on each act, kept in this browser's own
   storage (localStorage) under "sats-acts:<name>" as a list of act numbers. It never leaves the device; the privacy
   policy says so. Storage is touched only on the two pages that show the ticks. If the browser refuses storage, the
   tick boxes are not shown. */
(function () {
  "use strict";

  // ---- Send this explanation to a friend
  function wireShare(link) {
    var status = link.parentNode.querySelector(".share-done");
    var url = link.getAttribute("data-share-url");
    var title = link.getAttribute("data-share-title");
    function email() { window.location.href = link.href; }       // the link's own mailto: address
    function copy() {
      if (!(navigator.clipboard && navigator.clipboard.writeText)) { email(); return; }
      navigator.clipboard.writeText(url).then(function () {
        if (!status) return;
        status.textContent = status.getAttribute("data-copied");
        setTimeout(function () { status.textContent = ""; }, 4000);
      }, email);
    }
    link.addEventListener("click", function (ev) {
      ev.preventDefault();
      if (typeof navigator.share === "function") {
        var asked;
        try { asked = navigator.share({ title: title, url: url }); } catch (e) { copy(); return; }
        if (asked && typeof asked.then === "function") {
          // the reader closing the share sheet is an answer, not a failure; anything else falls back to copying
          asked.then(null, function (err) { if (!err || err.name !== "AbortError") copy(); });
        }
        return;
      }
      copy();
    });
  }
  var shares = document.querySelectorAll("[data-share]");
  for (var s = 0; s < shares.length; s++) wireShare(shares[s]);

  // ---- The knowledge check
  var check = document.querySelector("[data-check]");
  if (check) {
    var go = check.querySelector("[data-check-go]");
    var result = check.querySelector(".check-result");
    var sets = check.querySelectorAll("fieldset[data-answer]");
    var shown = check.querySelectorAll(".check-answer");
    for (var a = 0; a < shown.length; a++) shown[a].hidden = true;      // the button marks the answers instead
    if (go && result) {
      go.hidden = false;
      go.addEventListener("click", function () {
        var right = 0, unanswered = 0;
        for (var i = 0; i < sets.length; i++) {
          var set = sets[i];
          var picked = set.querySelector("input:checked");
          var why = set.querySelector(".why");
          var verdict = set.querySelector(".verdict");
          var answer = set.querySelector(".right-option");
          if (!picked) {
            unanswered++;
            set.removeAttribute("data-state");
            if (why) why.hidden = true;
            continue;
          }
          var ok = picked.value === set.getAttribute("data-answer");
          if (ok) right++;
          set.setAttribute("data-state", ok ? "right" : "wrong");
          if (verdict) verdict.textContent = check.getAttribute(ok ? "data-right" : "data-wrong");
          if (answer) answer.hidden = ok;                                 // name the right option after a wrong pick
          if (why) why.hidden = false;
        }
        result.textContent = unanswered
          ? check.getAttribute("data-unanswered")
          : check.getAttribute("data-score").replace("{right}", String(right)).replace("{total}", String(sets.length));
      });
    }
  }

  // ---- The twelve acts: ticks kept in this browser
  function storage() {
    try {
      var probe = "sats-acts:probe";
      window.localStorage.setItem(probe, "1");
      window.localStorage.removeItem(probe);
      return window.localStorage;
    } catch (e) { return null; }
  }
  // the saved list, cleaned: whole act numbers from 1 to `most`, each once, in order
  function readTicks(store, key, most) {
    try {
      var list = JSON.parse(store.getItem("sats-acts:" + key) || "[]");
      if (!Array.isArray(list)) return [];
      var seen = {}, out = [];
      for (var i = 0; i < list.length; i++) {
        var n = list[i];
        if (typeof n === "number" && n === Math.floor(n) && n >= 1 && n <= most && !seen[n]) { seen[n] = true; out.push(n); }
      }
      return out.sort(function (x, y) { return x - y; });
    } catch (e) { return []; }
  }
  function writeTicks(store, key, list) {
    try {
      if (list.length) store.setItem("sats-acts:" + key, JSON.stringify(list));
      else store.removeItem("sats-acts:" + key);
    } catch (e) { /* storage full or switched off: the ticks last for this visit only */ }
  }

  var panel = document.querySelector("[data-acts-progress]");
  var acts = document.querySelector("ol.acts");
  var summary = document.querySelector("[data-acts-summary]");
  var store = (panel && acts) || summary ? storage() : null;            // other pages never touch storage

  if (store && panel && acts) {
    var key = panel.getAttribute("data-acts-key");
    var label = panel.getAttribute("data-done-label");
    var items = acts.children;
    var ticks = readTicks(store, key, items.length);
    var boxes = [];
    var count = panel.querySelector("[data-acts-count]");
    var bar = panel.querySelector("progress");
    var clear = panel.querySelector("[data-acts-clear]");

    var render = function () {
      var done = 0;
      for (var i = 0; i < boxes.length; i++) {
        items[i].classList.toggle("is-done", boxes[i].checked);
        if (boxes[i].checked) done++;
      }
      if (count) count.textContent = String(done);
      if (bar) { bar.max = boxes.length; bar.value = done; }
      if (clear) clear.hidden = done === 0;
    };
    var save = function () {
      var list = [];
      for (var i = 0; i < boxes.length; i++) if (boxes[i].checked) list.push(i + 1);
      writeTicks(store, key, list);
      render();
    };

    for (var i = 0; i < items.length; i++) {
      var wrap = document.createElement("label");
      wrap.className = "act-done";
      var box = document.createElement("input");
      box.type = "checkbox";
      box.checked = ticks.indexOf(i + 1) !== -1;
      // each box says which act it belongs to, so twelve boxes are not all just "Done" to a screen reader
      var name = items[i].querySelector("strong");
      box.setAttribute("aria-label", label + ": " + (name ? name.textContent.replace(/\s+/g, " ").trim().replace(/[.:]$/, "") : "act " + (i + 1)));
      box.addEventListener("change", save);
      var text = document.createElement("span");
      text.textContent = label;
      wrap.appendChild(box);
      wrap.appendChild(text);
      items[i].appendChild(wrap);
      boxes.push(box);
    }
    if (clear) clear.addEventListener("click", function () {
      for (var i = 0; i < boxes.length; i++) boxes[i].checked = false;
      save();
      panel.focus();                                                      // the button hides itself; keep the reader's place
    });
    acts.parentNode.insertBefore(panel, acts);
    panel.hidden = false;
    render();
  }

  if (store && summary) {
    var showSummary = function () {
      var total = parseInt(summary.getAttribute("data-acts-total"), 10) || 12;
      var done = readTicks(store, summary.getAttribute("data-acts-key"), total).length;
      var n = summary.querySelector("[data-acts-count]");
      var p = summary.querySelector("progress");
      if (n) n.textContent = String(done);
      if (p) { p.max = total; p.value = done; }
      summary.hidden = done === 0;
    };
    showSummary();
    // a reader who ticks an act and comes back with the Back button gets the page as the browser kept it: count again
    window.addEventListener("pageshow", function (ev) { if (ev.persisted) showSummary(); });
  }
})();
