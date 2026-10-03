# Content

One folder per site. A Markdown file here becomes a page on that site; the folder it sits in is its section (the sections are listed in `sites/<site>/site.yml`).

| Folder | Site | What goes here |
| --- | --- | --- |
| `content/stats/` | faststatsforsats.com | `charts/` (one page per chart, template `chart`), `value/` (value explainers, under 400 words), `tools/` |
| `content/facts/` | fastfactsforsats.com | `basics/`, `network/`, `money/`, `rules/`, `safety/` explainers (template `guide`) |
| `content/acts/` | fastactsforsats.com | `buy/`, `earn/`, `store/`, `secure/`, `use/` how-to guides (template `guide`, with `understand_first`) |
| `content/shared/` | all three | The About page, the privacy policy, the affiliate disclosure, the terms of use, and the contact page: written once, built into every site at the same address, and linked from every footer through `footer_label`. No folders here. |

Each site's home page (`content/<site>/index.md`) keeps the words of its first screen in its front matter: the headline, the introduction, the button, and the cards. Those are Jim's words from his improvement plan of October 2026; the templates only lay them out. The five-minute guide on Facts (`content/facts/start.md`, template `route`) has no text of its own to keep in step: each stop names an explainer and the build lifts that page's words.

The front matter fields are documented at the top of `lib/content.py`. The writing rules are in the Project's style guide (claude/style-guide.md); the short version is in `CLAUDE.md` at the repository root.

The build fails on: a missing title, a page in a folder that is not a section, a `/go/` link to a slug that is not in `go/redirects.csv`, a `/go/` link on a page whose template has no place for the disclosure line, an em dash anywhere in the page, a picture that `shared/art.yml` does not list as approved, a guide stop that quotes a page or subhead that is not there, and a weekly chart or story that names no chart. It warns (and fails under `--strict`) when a question card quotes a sentence its page no longer has. It warns on a missing or long description, a title over 60 characters, an Acts guide without an "Understand first" line, and a `/go/` link to a program that is not yet approved.
