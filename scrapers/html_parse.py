from __future__ import annotations

from typing import Any

import requests

from .base import BaseScraper

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
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
    timeout = 15

    def request_kwargs(self) -> dict:
        return {"headers": DEFAULT_HEADERS}

    def fetch_raw(self) -> Any:
        resp = requests.request(self.method, self.url, timeout=self.timeout, **self.request_kwargs())
        resp.raise_for_status()
        return resp.text
