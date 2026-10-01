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
2. `python3 build.py <site>` renders them with the shared templates and stylesheet into `sites/<site>/dist/`, along with Cloudflare's `_redirects` (the `/go/` affiliate links), `_headers`, `robots.txt`, `sitemap.xml`, `feed.xml`, and a `404.html`.
3. Cloudflare Pages runs that command for each site on every push to `main` and on every pull request (which gets a preview address). Settings are below.
4. Every morning the Daily Build (GitHub Actions, step 16) pulls the public data sources, writes `data/`, draws `charts/`, and commits. That commit rebuilds the Stats site, which serves both folders.
5. Live numbers (price, fees) come from a Cloudflare Worker at api.faststatsforsats.com (step 15); `shared/static/live.js` swaps them into any page that asks, and leaves the daily figure in place when the API is unreachable.

## Folders

| Path | What is in it |
| --- | --- |
| `content/stats/`, `content/facts/`, `content/acts/` | The pages, one Markdown file each, with front matter (documented at the top of `lib/content.py`) |
| `sites/<site>/site.yml` | Each site's name, domain, tagline, sections, and settings |
| `sites/<site>/static/` | Files copied as-is into that site's root (favicon, images) |
| `sites/<site>/dist/` | Build output. Never committed; Cloudflare builds it |
| `shared/templates/` | Jinja2 templates shared by the three sites (`base`, `home`, `page`, `guide`, `chart`, `section`, `404`) |
| `shared/static/` | `site.css` and `live.js`, served at `/static/` on every site |
| `shared/_headers` | Cloudflare headers: open CORS and caching for `/charts/` and `/data/`, security headers elsewhere |
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

After the first deployment, set the build watch paths so a change to one site does not rebuild the other two (project Settings, Build, Build watch paths, Include paths). This keeps the daily data commit to one build a day instead of three, roughly 30 of the 500 free builds a month.

| Project | Include paths |
| --- | --- |
| faststatsforsats | `sites/stats/*`, `content/stats/*`, `shared/*`, `lib/*`, `go/*`, `data/*`, `charts/*`, `build.py`, `requirements.txt` |
| fastfactsforsats | `sites/facts/*`, `content/facts/*`, `shared/*`, `lib/*`, `go/*`, `build.py`, `requirements.txt` |
| fastactsforsats | `sites/acts/*`, `content/acts/*`, `shared/*`, `lib/*`, `go/*`, `build.py`, `requirements.txt` |

Then, for each project: Metrics, Enable Web Analytics. Custom domains are added in step 20 of the Build Recipe, after the pages.dev addresses have been reviewed.

If a build log ever says `externally-managed-environment`, add `--break-system-packages` after `install` in the build command. If it shows Python 3.11 or older, set the environment variable `PYTHON_VERSION` to `3.13` in the project's settings; the code runs on 3.10 and newer either way.

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

Code in this repository is under the MIT license (see `LICENSE`). The guides and charts carry the terms on each site's About page.
