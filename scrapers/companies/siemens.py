from __future__ import annotations

from typing import Any

import requests
from bs4 import BeautifulSoup

from ..base import JobPosting
from ..html_parse import DEFAULT_HEADERS, HtmlParseScraper


class SiemensScraper(HtmlParseScraper):
    company = "siemens"
    # Avature facet IDs baked into the query string (42414 = Germany country
    # facet) — reverse-engineered live via the actual search UI, not guessed.
    base_url = "https://jobs.siemens.com/en_US/externaljobs/SearchJobs/Munich/"
    page_size = 6  # server-enforced, ignores a larger folderRecordsPerPage

    def fetch_raw(self) -> Any:
        pages = []
        offset = 0
        while True:
            resp = requests.get(self.base_url, params={
                "42414": "[812132]",
                "42414_format": "17570",
                "listFilterMode": 1,
                "folderRecordsPerPage": self.page_size,
                "folderOffset": offset,
            }, headers=DEFAULT_HEADERS, timeout=self.timeout)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            articles = soup.select("article.article--result")
            if not articles:
                break
            pages.append(articles)
            if len(articles) < self.page_size:
                break
            offset += self.page_size
        return pages

    def parse(self, raw: Any) -> list[JobPosting]:
        postings = []
        for articles in raw:
            for art in articles:
                link = art.select_one("h3 a")
                if not link:
                    continue
                job_id_el = art.select_one(".list-item-jobId")
                job_id = job_id_el.get_text(strip=True).replace("Job ID:", "").strip() if job_id_el else None
                city = art.select_one(".list-item-jobCity")
                state = art.select_one(".list-item-jobState")
                country = art.select_one(".list-item-jobCountry")
                location = ", ".join(filter(None, [
                    city.get_text(strip=True) if city else None,
                    state.get_text(strip=True) if state else None,
                    country.get_text(strip=True) if country else None,
                ])) or None
                family = art.select_one(".list-item-family")
                href = link["href"]
                postings.append(JobPosting(
                    company=self.company,
                    external_id=job_id or href.rstrip("/").rsplit("/", 1)[-1],
                    title=link.get_text(strip=True),
                    # fuzzy keyword search (not a strict city facet) — feeding
                    # the card's own jobCity into `location` lets the standard
                    # filter_location() re-check double as the precision recheck
                    location=location,
                    url=href,
                    department=family.get_text(strip=True) if family else None,
                    posted_at=None,
                ))
        return postings


SCRAPER = SiemensScraper()
