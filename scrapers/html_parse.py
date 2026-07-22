from __future__ import annotations

from typing import Any

import requests

from targets.loader import load_target

from .base import BaseScraper

_cfg = load_target("base") or {}

DEFAULT_HEADERS = {
    "User-Agent": _cfg.get("user_agent", ""),
}


class HtmlParseScraper(BaseScraper):
    url: str
    method = "GET"
    timeout = _cfg.get("timeout_default", 15)

    def request_kwargs(self) -> dict:
        return {"headers": DEFAULT_HEADERS}

    def fetch_raw(self) -> Any:
        resp = requests.request(self.method, self.url, timeout=self.timeout, **self.request_kwargs())
        resp.raise_for_status()
        return resp.text
