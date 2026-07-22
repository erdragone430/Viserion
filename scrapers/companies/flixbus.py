from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from targets.loader import load_target

from ..base import JobPosting
from ..html_parse import HtmlParseScraper

_cfg = load_target("flixbus")


class FlixBusScraper(HtmlParseScraper):
    company = "flixbus"
    url = _cfg["endpoint"]

    def parse(self, raw: Any) -> list[JobPosting]:
        sel = _cfg["selectors"]
        base_url = _cfg["base_url"]
        fallback_loc = _cfg["fallback_location"]
        id_param = _cfg["id_param"]
        soup = BeautifulSoup(raw, "html.parser")
        postings = []
        for a in soup.select(sel["job_links"]):
            href = a["href"]
            if href.startswith("/"):
                href = f"{base_url}{href}"
            title_el = a.select_one(sel["title"])
            location_el = a.select_one(sel["location"])
            job_id = href.split(f"{id_param}=")[-1].split("&")[0] if f"{id_param}=" in href else href
            postings.append(JobPosting(
                company=self.company,
                external_id=job_id,
                title=title_el.get_text(strip=True) if title_el else "",
                location=location_el.get_text(strip=True) if location_el else fallback_loc,
                url=href,
                department=None,
                posted_at=None,
            ))
        return postings


SCRAPER = FlixBusScraper()
