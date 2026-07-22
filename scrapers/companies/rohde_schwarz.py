from __future__ import annotations

from typing import Any

import requests
from bs4 import BeautifulSoup

from targets.loader import load_target

from ..base import JobPosting
from ..html_parse import DEFAULT_HEADERS, HtmlParseScraper

_cfg = load_target("rohde_schwarz")


class RohdeSchwarzScraper(HtmlParseScraper):
    company = "rohde_schwarz"
    url = _cfg["endpoint"]
    page_size = _cfg["page_size"]

    def fetch_raw(self) -> Any:
        pages = []
        offset = 0
        params = _cfg["params"]
        while True:
            resp = requests.get(self.url, params={
                "term": params["term"],
                params["country_param"]: params["country"],
                params["city_param"]: params["city"],
                params["offset_param"]: offset,
            }, headers=DEFAULT_HEADERS, timeout=self.timeout)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select(_cfg["selectors"]["cards"])
            if not cards:
                break
            pages.append(cards)
            if len(cards) < self.page_size:
                break
            offset += self.page_size
        return pages

    def parse(self, raw: Any) -> list[JobPosting]:
        sel = _cfg["selectors"]
        keys = _cfg["label_keys"]
        url_tpl = _cfg["url_template"]
        postings = []
        for cards in raw:
            for card in cards:
                link = card.select_one(sel["title_link"])
                if not link:
                    continue
                fields = {}
                for item in card.select(sel["field_row"]):
                    label = item.select_one(sel["field_label"])
                    value = item.select_one(sel["field_value"])
                    if label and value:
                        fields[label.get_text(strip=True)] = value.get_text(strip=True)
                href = link["href"]
                if href.startswith("/"):
                    href = url_tpl.format(href=href)
                job_id = href.rstrip("/").rsplit("-", 1)[-1].replace(_cfg["id_pattern"], "")
                postings.append(JobPosting(
                    company=self.company,
                    external_id=job_id,
                    title=link.get_text(strip=True),
                    location=", ".join(filter(None, [fields.get(keys["city_region"]), fields.get(keys["location"])])) or None,
                    url=href,
                    department=fields.get(keys["functional_area"]),
                    posted_at=None,
                ))
        return postings


SCRAPER = RohdeSchwarzScraper()
