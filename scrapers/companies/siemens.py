from __future__ import annotations

from typing import Any

import requests
from bs4 import BeautifulSoup

from targets.loader import load_target

from ..base import JobPosting
from ..html_parse import DEFAULT_HEADERS, HtmlParseScraper

_cfg = load_target("siemens")


class SiemensScraper(HtmlParseScraper):
    company = "siemens"
    base_url = _cfg["base_url"]
    page_size = _cfg["page_size"]

    def fetch_raw(self) -> Any:
        pages = []
        offset = 0
        facets = {}
        for f in _cfg["facets"].values():
            facets[f["param"]] = f["value"]
            facets[f"{f['param']}_format"] = f["format"]
        while True:
            resp = requests.get(self.base_url, params={
                **facets,
                "listFilterMode": 1,
                "folderRecordsPerPage": self.page_size,
                "folderOffset": offset,
            }, headers=DEFAULT_HEADERS, timeout=self.timeout)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            articles = soup.select(_cfg["selectors"]["article_selector"])
            if not articles:
                break
            pages.append(articles)
            if len(articles) < self.page_size:
                break
            offset += self.page_size
        return pages

    def filter_location(self, postings):
        return postings

    def parse(self, raw: Any) -> list[JobPosting]:
        sel = _cfg["selectors"]
        label = _cfg["id_label"]
        postings = []
        for articles in raw:
            for art in articles:
                link = art.select_one(sel["title_link"])
                if not link:
                    continue
                job_id_el = art.select_one(sel["job_id"])
                job_id = job_id_el.get_text(strip=True).replace(label, "").strip() if job_id_el else None
                city = art.select_one(sel["city"])
                state = art.select_one(sel["state"])
                country = art.select_one(sel["country"])
                if city:
                    location = ", ".join(filter(None, [
                        city.get_text(strip=True),
                        state.get_text(strip=True) if state else None,
                        country.get_text(strip=True) if country else None,
                    ])) or None
                else:
                    loc_el = art.select_one(sel["location_multi"])
                    location = loc_el.get_text(strip=True) if loc_el else None
                family = art.select_one(sel["department"])
                href = link["href"]
                postings.append(JobPosting(
                    company=self.company,
                    external_id=job_id or href.rstrip("/").rsplit("/", 1)[-1],
                    title=link.get_text(strip=True),
                    location=location,
                    url=href,
                    department=family.get_text(strip=True) if family else None,
                    posted_at=None,
                ))
        return postings


SCRAPER = SiemensScraper()
