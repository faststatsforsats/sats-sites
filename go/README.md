# The /go/ redirect table

Every affiliate link on the three sites is written as `/go/{slug}`. Nothing else. For an approved program the build writes a rule into Cloudflare's `_redirects` file for each site, so `/go/kraken` on any of the three domains sends the reader to the URL in the `url` column with a 302.

Why: when a program approves us, the tracking link is pasted into this one file and every page is correct on the next build. When a program changes its link or closes, same thing. Readers never see a raw affiliate URL, and a link that was published never dies.

What `/go/{slug}` does, by status:

| Status | What the reader gets |
| --- | --- |
| `approved` | A 302 to the `url` column (the tracking link). |
| `closed` | A 302 to the `url` column. Set it back to the merchant's plain page when a program ends, so links already out in newsletters and posts keep working. |
| `not applied`, `applied`, `declined` | No redirect. The build writes a small page at `/go/{slug}/` that says the link is not live (`shared/templates/go_pending.html`): "not live yet" while a link may still arrive, "not live" for a declined program. It names the program, carries `noindex`, and links the home page. |

Cloudflare follows a redirect even when a file exists at the same address, so the build gives each slug one or the other (`lib/redirects.py`). The affiliate disclosure page on every site lists the programs whose status is `approved`, from this table, on each build.

## Columns

| Column | Meaning |
| --- | --- |
| slug | Lowercase letters, digits, hyphens. The part after `/go/`. Never rename a slug that has been published; add a new row instead. |
| program | The program's name as it appears in claude/affiliate-programs.md. |
| status | `not applied`, `applied`, `approved`, `declined`, `closed`. Placement boxes (the `placements:` list in a page's front matter) render only for `approved`. A plain `/go/` link in page text to a program that is not approved lands on the "not live" page, and the build prints a warning (an error under `--strict`). |
| url | The destination. Plain merchant home page until approval (kept on file; nothing links to it), then the tracking link. |
| campaign | Optional. For a campaign-specific link make a new row, for example `kraken-first100k`, so clicks can be told apart in the program's dashboard. |
| notes | Anything the next person needs to know. |

## Rules

- The CSV is the only place a tracking link lives in this repository. Never paste one into a page.
- One row per slug. The build fails on a duplicate slug or a page that links to a slug that is not here.
- Keep statuses in step with claude/affiliate-programs.md (the Analyst agent checks this weekly).
- Change the status and the url together. A tracking link under any status but `approved` does nothing, and `approved` over a plain home page redirects without earning anything.
- A `/go/` link written in a page body must sit on a page whose template prints the disclosure line (`page`, `guide`, `chart`, `campaign`); the build fails otherwise. Placement boxes carry the line themselves.
- Cloudflare Pages allows 2,000 static redirects per site; this table will not get near that.
