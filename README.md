# sats-sites

Fast Stats, Fast Facts, and Fast Acts for Sats: three small sites built from one repository.

| Site | Domain | What it is for |
| --- | --- | --- |
| Stats | faststatsforsats.com | Graphics and easy-to-understand details about the value of sats and bitcoin. Charts first, a short explainer beside each. Publishes the shared data and chart files. |
| Facts | fastfactsforsats.com | How bitcoin works, in plain language. |
| Acts | fastactsforsats.com | How to buy, earn, store, secure, and use bitcoin. Most affiliate placements live here. |

Sats means satoshis, the smallest unit of bitcoin. Every page says so, and no page gives financial advice.

## How it works

1. Pages are Markdown files under `content/<site>/`. The folder a file sits in is its section.
2. `python3 build.py <site>` renders them with the shared templates and stylesheet into `sites/<site>/dist/`, along with Cloudflare's `_redirects` (the `/go/` links of approved programs), a "not live" page for every other `/go/` link, `_headers`, `robots.txt`, `sitemap.xml`, `feed.xml`, and a `404.html`. Five pages are written once in `content/shared/` and built into all three sites: the About page, the privacy policy, the affiliate disclosure, the terms of use, and the contact page. Every footer links them.
3. Cloudflare Pages runs that command for each site on every push to `main` and on every pull request (which gets a preview address). Settings are below.
4. Every morning the Daily Build (GitHub Actions, step 16) pulls the public data sources, writes `data/`, draws `charts/`, and commits. That commit rebuilds the Stats site, which serves both folders.
5. Live numbers (price, fees) come from a Cloudflare Worker at api.faststatsforsats.com (step 15); `shared/static/live.js` swaps them into any page that asks, and leaves the daily figure in place when the API is unreachable.

## Folders

| Path | What is in it |
| --- | --- |
| `content/stats/`, `content/facts/`, `content/acts/` | The pages, one Markdown file each, with front matter (documented at the top of `lib/content.py`) |
| `content/shared/` | Pages every site carries at the same address: `/about/`, `/privacy/`, `/affiliate-disclosure/`, `/terms/`, `/contact/` |
| `sites/<site>/site.yml` | Each site's name, domain, tagline, sections, and settings |
| `sites/<site>/static/` | Files copied as-is into that site's root (favicon, images). On Stats this includes `embed.js`, the sats badge script other sites load from https://faststatsforsats.com/embed.js |
| `sites/<site>/dist/` | Build output. Never committed; Cloudflare builds it |
| `shared/templates/` | Jinja2 templates shared by the three sites (`base`, `home` and one first screen per site: `home_stats`, `home_facts`, `home_acts`; `page`, `guide`, `route`, `chart`, `campaign`, `section`, `404`) |
| `shared/static/` | `site.css`, `live.js`, `converter.js`, `embeds.js` (copy buttons and the badge form), and `actions.js` (send to a friend, the knowledge check, the twelve acts' tick boxes), served at `/static/` on every site. `shared/static/brand/` holds the three coins, each as a PNG and a light WebP copy (`scripts/brand.py`); the header offers the copy first, and `shared/brand.json` records the PNG each copy was made from and the copy itself, so the build never offers a copy that is out of date |
| `shared/art.yml`, `art/masters/`, `shared/static/art/` | The illustrations: one entry per picture (alt text, the caption, where it goes, its source and status), the master as supplied, and the web copies `scripts/art.py` makes from it. See "Pictures" below |
| `shared/_headers` | Cloudflare headers: open CORS and caching for `/charts/`, `/data/`, and `/embed.js`, security headers elsewhere, and `noindex` on the pages.dev addresses so only the real domains reach search results |
| `shared/sites.yml` | The three sites, for the header and footer cross-links |
| `go/redirects.csv` | The `/go/{slug}` affiliate redirect table. See `go/README.md` |
| `data/` | JSON written by the Daily Build. See `data/README.md` |
| `charts/` | PNG and SVG charts drawn by the Daily Build, plus `index.json`. See `charts/README.md` |
| `lib/` | The build (`site.py`, `content.py`, `redirects.py`) and the shared chart style (`chartstyle.py`) |
| `build.py` | The command Cloudflare and you run |
| `workers/` | The live-data Worker (step 15) |
| `scripts/` and `.github/workflows/daily-build.yml` | The Daily Build (step 16) |
| `.github/workflows/build-check.yml` | Builds all three sites on every pull request so a broken page cannot be merged |
| `CLAUDE.md` | The working rules for Claude sessions that edit this repository |

## Cloudflare Pages settings

Three Pages projects, all connected to this repository (Workers & Pages, Create application, Pages, Connect to Git, pick `sats-sites`). Framework preset: None. Production branch: `main`. Root directory: leave empty, so every build starts at the repository root. No environment variables. The build system version should be the current default (v3, Python 3.13); nothing here needs a specific version.

| Setting | faststatsforsats | fastfactsforsats | fastactsforsats |
| --- | --- | --- | --- |
| Project name | `faststatsforsats` | `fastfactsforsats` | `fastactsforsats` |
| Root directory | empty | empty | empty |
| Build command | `python3 -m pip install -r requirements.txt && python3 build.py stats` | `python3 -m pip install -r requirements.txt && python3 build.py facts` | `python3 -m pip install -r requirements.txt && python3 build.py acts` |
| Build output directory | `sites/stats/dist` | `sites/facts/dist` | `sites/acts/dist` |

To change a field after the first deployment: the project's Settings, Build, Edit under Build configuration, Save, then Deployments, Retry deployment.

If a build log ever says `externally-managed-environment`, add `--break-system-packages` after `install` in the build command. If it shows Python 3.11 or older, set the environment variable `PYTHON_VERSION` to `3.13` in the project's settings; the code runs on 3.10 and newer either way.

After the first deployment, set the build watch paths so a change to one site does not rebuild the other two (project Settings, Build, Build watch paths, Include paths). This keeps the daily data commit to the sites that use the data instead of all three.

| Project | Include paths |
| --- | --- |
| faststatsforsats | `sites/stats/*`, `content/stats/*`, `content/shared/*`, `shared/*`, `lib/*`, `go/*`, `data/*`, `charts/*`, `build.py`, `requirements.txt` |
| fastfactsforsats | `sites/facts/*`, `content/facts/*`, `content/shared/*`, `shared/*`, `lib/*`, `go/*`, `build.py`, `requirements.txt` |
| fastactsforsats | `sites/acts/*`, `content/acts/*`, `content/shared/*`, `shared/*`, `lib/*`, `go/*`, `charts/*`, `build.py`, `requirements.txt` |

`content/shared/*` is on every list because the pages written once for all three sites (About, privacy, affiliate disclosure, terms, contact) live there; without it, an edit to one of them would not rebuild a site until something else changed.

The Acts list includes `charts/*` because a campaign page (`template: campaign`) shows one Stats chart as its hook and the build copies that chart's images from `charts/`; without it the chart on the campaign page would refresh only when something else on the Acts site changed. The daily data commit therefore rebuilds Stats and Acts, about 60 of the 500 free builds a month.

Then, for each project: Metrics, Enable Web Analytics. Custom domains are added in step 20 of the Build Recipe, after the pages.dev addresses have been reviewed: in each project, Custom domains, Set up a domain, the bare domain and then `www.` in front of it. The pages.dev addresses keep working afterwards; `shared/_headers` marks them `noindex`.

## Embeds

Other sites can show two things from Stats, and https://faststatsforsats.com/tools/embed/ shows both the way another site would, with the code to copy:

- A chart: an `<img>` of `https://faststatsforsats.com/charts/<slug>.png` inside a link to the chart's page, with the credit line "Chart by Fast Stats for Sats". Each chart page offers its own code; the one definition is `chart_snippet` in `shared/templates/_embed.html`.
- The sats badge: a link with `class="sats-badge"`, `data-amount`, `data-currency`, and an optional `data-label`, followed by `<script async src="https://faststatsforsats.com/embed.js">`. The script (`sites/stats/static/embed.js`) reads the hourly price from api.faststatsforsats.com and turns the link into a badge with the amount in sats, the time of the price, and the credits. It sets no cookies and stores nothing; if the price cannot be reached the plain link stays. The embed page's form writes the code, and `?amount=4.5&currency=usd&label=Flat%20white` on its address opens it on that price.

`embed.js` is a public address that other sites depend on. Keep the markup it reads (`a.sats-badge` and the three `data-` attributes) working when you change it.

## Pictures

The illustrations are a series: still lifes on navy with orange details, no people, one visual joke each. `shared/art.yml` lists them, with every word that goes with a picture (the alt text, the quoted line under it, the bridge to the next topic). A page shows one with `[[art:<name>]]` in its Markdown, or names it in its front matter (`art:` on a chart page, `hero.art` on a home page, `art:` on a Stats story card).

Each picture is served whole, at 3:2, in four widths (480, 768, 1080, 1536 px) as WebP with a 1080 px JPEG behind them; the page tells the browser how wide the picture is shown and the browser picks a file. A picture near the top of a page loads at once; one further down waits until the reader scrolls near it. Captions, bridges, and buttons are text on the page, never part of the picture, so they can be read aloud, translated, and edited without redrawing anything.

To add one: put the master in `art/masters/<name>.png`, add its entry to `shared/art.yml` with status `prepared`, run `python3 scripts/art.py <name>`, and commit all three. Change the status to `approved` when Jim has seen it in its place; the build refuses a page that shows a picture before then.

## Phones

The pages are laid out for a 360 px screen first and checked at 320 px. Four things to keep when changing `shared/static/site.css`: a table of numbers must show its figures on a phone (cells tighten, headings wrap, a column that only repeats another gives way through `hide-sm`, and what is still too wide scrolls sideways with a shadow at the edge; it is never cut off); an element with the `hidden` attribute stays hidden whatever class it carries; the header keeps to three short rows (the three sites, the logo, the menu in one row that scrolls sideways); and the picture that opens a chart page stays small, with its quoted line beside it, so the chart starts on the first screen.

## Build it yourself

```
python3 -m pip install -r requirements.txt
python3 build.py all
python3 -m http.server -d sites/stats/dist 8001     # then open http://localhost:8001
```

`python3 build.py all --strict` treats warnings as errors; the pull request check runs it that way. `python3 -m lib.chartstyle --demo out/` draws a sample chart (labeled as sample data) to look at the chart style.

## The one rule about affiliate links

Every affiliate link on every page is written as `/go/{slug}`, with the slug taken from `go/redirects.csv`. The tracking link itself is pasted into that CSV on approval and nowhere else. The build fails on a slug it does not know, and placement boxes render only for programs whose status is `approved`.

## Working on it

Claude opens a pull request for each change; Cloudflare adds a preview link to the pull request and the build check adds a green check mark. Open the preview, read the page, and select Merge pull request, then Confirm merge. The sites rebuild from `main` within a few minutes.

Code in this repository is under the MIT license (see `LICENSE`). The text, charts, and badge carry the terms on each site's `/terms/` page (`content/shared/terms.md`).
