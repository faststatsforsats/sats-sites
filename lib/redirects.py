"""The /go/ affiliate redirect table (go/redirects.csv) and Cloudflare's _redirects file.

What /go/<slug> does depends on the row's status:
    approved                         -> 302 to the url column (the tracking link)
    closed                           -> 302 to the url column (set it back to the merchant's plain page), so a link that
                                        was published while the program ran never dies
    not applied, applied, declined   -> no redirect; the build writes a small page at /go/<slug>/ that says the link is
                                        not live (shared/templates/go_pending.html)
Cloudflare follows a redirect even when a file exists at the same address, so a slug gets one or the other, never both.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
STATUSES = {"not applied", "applied", "approved", "declined", "closed"}
FORWARDING = {"approved", "closed"}   # statuses whose /go/<slug> is a redirect


@dataclass(frozen=True)
class Redirect:
    slug: str
    program: str
    status: str
    url: str
    campaign: str = ""
    notes: str = ""

    @property
    def approved(self) -> bool:
        return self.status == "approved"

    @property
    def forwards(self) -> bool:
        """True when /go/<slug> sends the reader on to the url column; otherwise the build writes the "not live" page."""
        return self.status in FORWARDING

    @property
    def expected(self) -> bool:
        """True while a link may still arrive (not applied, applied): the "not live" page says "yet"."""
        return self.status in ("not applied", "applied")


def load_redirects(csv_path: Path) -> dict[str, Redirect]:
    rows: dict[str, Redirect] = {}
    with csv_path.open(newline="", encoding="utf-8") as handle:
        for number, raw in enumerate(csv.DictReader(handle), start=2):
            slug = (raw.get("slug") or "").strip().lower()
            if not slug:
                raise ValueError(f"{csv_path}:{number}: empty slug")
            if not SLUG.match(slug):
                raise ValueError(f"{csv_path}:{number}: slug {slug!r} may use lowercase letters, digits, and hyphens only")
            if slug in rows:
                raise ValueError(f"{csv_path}:{number}: duplicate slug {slug!r}")
            status = (raw.get("status") or "not applied").strip().lower()
            if status not in STATUSES:
                raise ValueError(f"{csv_path}:{number}: status {status!r} must be one of {sorted(STATUSES)}")
            url = (raw.get("url") or "").strip()
            if not url.startswith("https://"):
                raise ValueError(f"{csv_path}:{number}: url for {slug!r} must start with https://")
            rows[slug] = Redirect(
                slug=slug,
                program=(raw.get("program") or "").strip(),
                status=status,
                url=url,
                campaign=(raw.get("campaign") or "").strip(),
                notes=(raw.get("notes") or "").strip(),
            )
    return rows


def render_redirects_file(redirects: dict[str, Redirect]) -> str:
    """Cloudflare Pages _redirects: one rule per line, `source destination status`. Only approved and closed programs."""
    lines = [
        "# Generated from go/redirects.csv by build.py. Edit the CSV, not this file.",
        "# Format: /go/<slug>  <destination>  302",
    ]
    forwarding = [slug for slug in sorted(redirects) if redirects[slug].forwards]
    if not forwarding:
        lines.append("# No program is approved yet, so there is nothing to redirect: every /go/<slug>/ is the \"not live\" page.")
    for slug in forwarding:
        target = redirects[slug]
        lines.append(f"/go/{slug} {target.url} 302")
        lines.append(f"/go/{slug}/ {target.url} 302")
    return "\n".join(lines) + "\n"
