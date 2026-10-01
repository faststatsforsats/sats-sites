"""Small HTTP helper shared by the sources: retries, a polite user agent, and an offline fixtures mode.

Fixtures mode (``python3 scripts/daily_build.py --fixtures``) answers every request from scripts/fixtures/
instead of the network, so the whole pipeline can be run and tested without keys or connectivity.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

USER_AGENT = "faststatsforsats.com daily build (https://faststatsforsats.com; jim@faststatsforsats.com)"
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
TIMEOUT = 60


class SourceError(Exception):
    """A source could not be read. The message is meant for the build log."""


def fixtures_on() -> bool:
    return os.environ.get("SATS_FIXTURES") == "1"


def _fixture(name: str, as_text: bool = False):
    path = FIXTURES_DIR / name
    if not path.exists():
        raise SourceError(f"fixtures mode: no fixture named {name}")
    return path.read_text(encoding="utf-8") if as_text else json.loads(path.read_text(encoding="utf-8"))


def get_json(url: str, *, fixture: str, params: dict | None = None, headers: dict | None = None, tries: int = 3):
    if fixtures_on():
        return _fixture(fixture)
    return _request("GET", url, params=params, headers=headers, tries=tries).json()


def post_json(url: str, payload: dict, *, fixture: str, headers: dict | None = None, tries: int = 3):
    if fixtures_on():
        return _fixture(fixture)
    return _request("POST", url, json=payload, headers=headers, tries=tries).json()


def get_text(url: str, *, fixture: str, params: dict | None = None, headers: dict | None = None, tries: int = 3) -> str:
    if fixtures_on():
        return _fixture(fixture, as_text=True)
    return _request("GET", url, params=params, headers=headers, tries=tries).text


def get_bytes(url: str, *, fixture: str, headers: dict | None = None, tries: int = 3) -> bytes:
    if fixtures_on():
        return (FIXTURES_DIR / fixture).read_bytes()
    return _request("GET", url, headers=headers, tries=tries).content


def _request(method: str, url: str, *, tries: int, **kwargs) -> requests.Response:
    headers = {"user-agent": USER_AGENT, "accept": "application/json, text/csv, */*"}
    headers.update(kwargs.pop("headers", None) or {})
    last = None
    for attempt in range(1, tries + 1):
        try:
            res = requests.request(method, url, headers=headers, timeout=TIMEOUT, **kwargs)
            if res.status_code == 429 or res.status_code >= 500:
                last = SourceError(f"{url} answered {res.status_code}")
            else:
                res.raise_for_status()
                return res
        except requests.RequestException as err:
            last = SourceError(f"{url}: {err}")
        if attempt < tries:
            time.sleep(3 * attempt)
    raise last or SourceError(f"{url}: no response")
