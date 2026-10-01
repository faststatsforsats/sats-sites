# Working rules for this repository

This repository builds three sites for Jim Shaver: Fast Stats for Sats (faststatsforsats.com, the value of sats and bitcoin, charts first), Fast Facts for Sats (fastfactsforsats.com, how bitcoin works), and Fast Acts for Sats (fastactsforsats.com, how to buy, earn, store, secure, and use bitcoin). The full plan, style guide, backlog, and affiliate list live in the claude.ai Project "Alternate domains for experiements"; the short version you need is here.

## Build and check

- `python3 -m pip install -r requirements.txt` then `python3 build.py all --strict`. The build must exit 0 before a pull request is opened.
- Output goes to `sites/<site>/dist/`, which is ignored by git. Never commit it.
- `README.md` holds the Cloudflare Pages settings. If you change the build command or output folder, change the README in the same pull request.

## Where things go

- A page is a Markdown file under `content/<site>/<section>/<slug>.md`. Front matter fields are documented at the top of `lib/content.py`. Sections are declared in `sites/<site>/site.yml`; add a section there before adding a folder.
- Templates: `shared/templates/`. Styles: `shared/static/site.css`. Chart style: `lib/chartstyle.py`. Redirects: `go/redirects.csv`.
- Data and charts are written only by the Daily Build. Do not edit `data/` or `charts/` by hand.

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
