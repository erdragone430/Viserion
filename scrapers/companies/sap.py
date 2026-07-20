from __future__ import annotations

import random
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

from ..base import JobPosting
from ..html_parse import DEFAULT_HEADERS, HtmlParseScraper


class SapScraper(HtmlParseScraper):
    company = "sap"
    url = "https://jobs.sap.com/search/"
    page_size = 25

    def fetch_raw(self) -> Any:
        pages = []
        startrow = 0
        while True:
            # ponytail: jobs.sap.com runs PerimeterX bot mitigation. A cold
            # curl wasn't blocked in testing, but we only poll hourly anyway,
            # so a few seconds of jitter before this one request is cheap
            # insurance. If this scraper starts failing intermittently in
            # prod, PerimeterX escalating is the first thing to check —
            # the Phase 1 health-alert system will surface that as 3+
            # consecutive failures same as any other broken scraper.
            time.sleep(random.uniform(2, 5))
            resp = requests.get(self.url, params={
                "q": "",
                "locationsearch": "Munich",
                "startrow": startrow,
            }, headers=DEFAULT_HEADERS, timeout=self.timeout)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.select("table tr.data-row")
            if not rows:
                break
            pages.append(rows)
            if len(rows) < self.page_size:
                break
            startrow += self.page_size
        return pages

    def parse(self, raw: Any) -> list[JobPosting]:
        postings = []
        for rows in raw:
            for row in rows:
                link = row.select_one("td.colTitle a.jobTitle-link")
                loc = row.select_one("td.colLocation span.jobLocation")
                if not link:
                    continue
                href = link["href"]
                if href.startswith("/"):
                    href = f"https://jobs.sap.com{href}"
                job_id = href.rstrip("/").rsplit("/", 1)[-1]
                postings.append(JobPosting(
                    company=self.company,
                    external_id=job_id,
                    title=link.get_text(strip=True),
                    location=loc.get_text(strip=True) if loc else None,
                    url=href,
                    department=None,
                    posted_at=None,
                ))
        return postings


SCRAPER = SapScraper()
