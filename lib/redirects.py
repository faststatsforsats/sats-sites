"""The /go/ affiliate redirect table (go/redirects.csv) and Cloudflare's _redirects file."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
STATUSES = {"not applied", "applied", "approved", "declined", "closed"}


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
    """Cloudflare Pages _redirects: one rule per line, `source destination status`."""
    lines = [
        "# Generated from go/redirects.csv by build.py. Edit the CSV, not this file.",
        "# Format: /go/<slug>  <destination>  302",
    ]
    for slug in sorted(redirects):
        target = redirects[slug]
        lines.append(f"/go/{slug} {target.url} 302")
        lines.append(f"/go/{slug}/ {target.url} 302")
    return "\n".join(lines) + "\n"
