from __future__ import annotations

from typing import Any

import requests

from targets.loader import load_target

from .base import BaseScraper

_cfg = load_target("base")

DEFAULT_HEADERS = {
    "User-Agent": _cfg["user_agent"],
}


class HtmlParseScraper(BaseScraper):
    """Base for scrapers backed by plain HTTP GET + HTML parsing (BeautifulSoup).

    Same fetch_raw()/parse()/filter_location() contract as DirectJsonScraper —
    fetch_raw() just returns HTML text instead of JSON. Companies that need
    pagination override fetch_raw() themselves (see siemens.py/sap.py/etc),
    same pattern as Amazon in Phase 1.
    """

    url: str
    method = "GET"
    timeout = _cfg.get("timeout_default", 15)

    def request_kwargs(self) -> dict:
        return {"headers": DEFAULT_HEADERS}

    def fetch_raw(self) -> Any:
        resp = requests.request(self.method, self.url, timeout=self.timeout, **self.request_kwargs())
        resp.raise_for_status()
        return resp.text
