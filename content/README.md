# Content

One folder per site. A Markdown file here becomes a page on that site; the folder it sits in is its section (the sections are listed in `sites/<site>/site.yml`).

| Folder | Site | What goes here |
| --- | --- | --- |
| `content/stats/` | faststatsforsats.com | `charts/` (one page per chart, template `chart`), `value/` (value explainers, under 400 words), `tools/` |
| `content/facts/` | fastfactsforsats.com | `basics/`, `network/`, `money/`, `rules/`, `safety/` explainers (template `guide`) |
| `content/acts/` | fastactsforsats.com | `buy/`, `earn/`, `store/`, `secure/`, `use/` how-to guides (template `guide`, with `understand_first`) |

The front matter fields are documented at the top of `lib/content.py`. The writing rules are in the Project's style guide (claude/style-guide.md); the short version is in `CLAUDE.md` at the repository root.

The build fails on: a missing title, a page in a folder that is not a section, a `/go/` link to a slug that is not in `go/redirects.csv`, and an em dash anywhere in the page. It warns on a missing or long description, a title over 60 characters, an Acts guide without an "Understand first" line, and a `/go/` link to a program that is not yet approved.
