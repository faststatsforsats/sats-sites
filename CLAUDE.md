# Working rules for this repository

This repository builds three sites for Jim Shaver: Fast Stats for Sats (faststatsforsats.com, the value of sats and bitcoin, charts first), Fast Facts for Sats (fastfactsforsats.com, how bitcoin works), and Fast Acts for Sats (fastactsforsats.com, how to buy, earn, store, secure, and use bitcoin). The full plan, style guide, backlog, and affiliate list live in the claude.ai Project "Alternate domains for experiements"; the short version you need is here.

## Build and check

- `python3 -m pip install -r requirements.txt` then `python3 build.py all --strict`. The build must exit 0 before a pull request is opened.
- Output goes to `sites/<site>/dist/`, which is ignored by git. Never commit it.
- `README.md` holds the Cloudflare Pages settings. If you change the build command or output folder, change the README in the same pull request.

## Where things go

- A page is a Markdown file under `content/<site>/<section>/<slug>.md`. Front matter fields are documented at the top of `lib/content.py`. Sections are declared in `sites/<site>/site.yml`; add a section there before adding a folder.
- Templates: `shared/templates/`. Styles: `shared/static/site.css`. Chart style: `lib/chartstyle.py`. Redirects: `go/redirects.csv`.
- Data and charts are written only by the Daily Build (`scripts/daily_build.py`, 09:00 UTC). Do not edit `data/` or `charts/` by hand.
- The Stats site reads `data/` and `charts/` at build time through `lib/stats_data.py` (the `stats` object in templates) and generates `/sats/<amount>-<currency>/` and `/items/<slug>/` pages from them in `lib/site.py`. A top-level page joins the header nav with `nav: true` and a short `nav_label`.
- A page can show today's figure with a token in its Markdown: `[[live:sats-per-dollar]]`, `[[live:price]]`, `[[live:sats-for:100:usd]]`, `[[live:money-for:100000]]`, `[[live:fee:fast]]`, `[[live:height]]`, `[[live:to-halving]]`, `[[live:supply]]`, `[[live:when]]` (or `[[live:when:fees]]`), `[[live:cpi]]`, `[[live:gold]]`. The build bakes the number from `data/latest.json` and `shared/static/live.js` refreshes it from the Worker; the full list is `expand_live` in `lib/site.py`.
- Placement boxes (`placements:` in front matter) may name a program before it is approved; the box and the disclosure line appear only once `go/redirects.csv` says `approved`. A `/go/` link written in the body must already be approved or the strict build fails.
- Chart pages under `content/stats/charts/` are shared with the Daily Build: it owns the `chart` and `updated` front matter and the text between `<!-- auto:start -->` and `<!-- auto:end -->`. Write the explainer below the end marker and it is kept.

## Brand

- Jim's logos are the three coin renders (B plus a bar chart, a document, a lightning bolt) and the wordmarks "Fast Stats for Sats", "Fast Facts for Sats", "Fast Acts for Sats" with the middle word in orange. The header shows the coin and the wordmark image; never retype the site name as text in the header.
- Colors (tokens in `shared/static/site.css`): navy `#071829` for the header and footer band (the logo background), wordmark orange `#f97e1b` as the accent, `#b85300` when orange must read as small text on white, link blue `#0b63b5`; dark mode uses navy `#0b1a2b` pages with `#ffa14a` and `#5cc3ff`. Charts use the same palette (`lib/chartstyle.py`): orange first, blue second, and the Stats coin in the footer corner. The chart look (highlighted figure in the title, glow line and wash, latest-value pill, marked highs and lows, halving lines) lives in `lib/chartstyle.py` and `scripts/chartbook.py`; redraw from saved data with `python3 scripts/daily_build.py --offline`.
- Assets: `shared/static/brand/<site>-coin.png` (112 px, transparent, used by every site for the family links), `sites/<site>/static/brand/` (wordmark.png, og.png 1200 by 630, coin-512.png for profiles), and the favicons in `sites/<site>/static/`. The source renders live with Jim; ask before redrawing anything.

## Writing rules (from the style guide)

- Write like a person talking to a smart friend. Short sentences, paragraphs of three sentences or fewer, American spelling, digits with units (4,100 sats, $79, 12%).
- Never use an em dash. The build fails on one. Use a comma, colon, semicolon, or period.
- Never use: streamline, seamless, delve, leverage, unlock, game-changer, revolutionary, empower, robust, cutting-edge, journey, ecosystem (as filler), unleash.
- The answer comes first: the first two sentences of a guide answer the question in its title.
- Bitcoin the network is capitalized; bitcoin the asset is lowercase; sats is lowercase. Explain "sats" the first time it appears on a page.
- No price predictions, no targets, no "will." No advice on how much anyone should buy, hold, or allocate.
- Every figure comes from `data/` or a named source with a URL and a pull time. No estimates.
- Every Acts guide has `understand_first` in its front matter, linking the Facts explainer behind it.
- Affiliate links are written only as `/go/{slug}` and only for programs with status `approved` in `go/redirects.csv`. Never a raw affiliate URL. Placement boxes go in the `placements:` front matter list, not in the body.
- Tax and IRA pages describe general rules and say a tax professional should be consulted for the reader's situation.

## Pull requests

- One topic per pull request, a title that says what changed, and a description Jim can read in a minute: what the change is, which pages it touches, and anything he should check in the preview.
- Never merge. Jim merges after reading the preview.
- Never commit a secret. Keys live in GitHub's secrets store (`COINGECKO_KEY`, `BLS_KEY`, `FRED_KEY`, `NOSTR_NSEC`) and in Cloudflare's Worker secrets.
