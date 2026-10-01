# The /go/ redirect table

Every affiliate link on the three sites is written as `/go/{slug}`. Nothing else. The build turns this table into Cloudflare's `_redirects` file for each site, so `/go/kraken` on any of the three domains sends the reader to the URL in the `url` column with a 302.

Why: when a program approves us, the tracking link is pasted into this one file and every page is correct on the next build. When a program changes its link or closes, same thing. Readers never see a raw affiliate URL, and a dead program never leaves a dead link: until approval, the slug points at the merchant's plain home page.

## Columns

| Column | Meaning |
| --- | --- |
| slug | Lowercase letters, digits, hyphens. The part after `/go/`. Never rename a slug that has been published; add a new row instead. |
| program | The program's name as it appears in claude/affiliate-programs.md. |
| status | `not applied`, `applied`, `approved`, `declined`, `closed`. Placement boxes (the `placements:` list in a page's front matter) render only for `approved`. A plain `/go/` link in page text works at any status but the build prints a warning when the program is not approved. |
| url | The destination. Plain merchant home page until approval, then the tracking link. |
| campaign | Optional. For a campaign-specific link make a new row, for example `kraken-first100k`, so clicks can be told apart in the program's dashboard. |
| notes | Anything the next person needs to know. |

## Rules

- The CSV is the only place a tracking link lives in this repository. Never paste one into a page.
- One row per slug. The build fails on a duplicate slug or a page that links to a slug that is not here.
- Keep statuses in step with claude/affiliate-programs.md (the Analyst agent checks this weekly).
- Cloudflare Pages allows 2,000 static redirects per site; this table will not get near that.
