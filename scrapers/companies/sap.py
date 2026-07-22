from __future__ import annotations

import random
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

from targets.loader import load_target

from ..base import JobPosting
from ..html_parse import DEFAULT_HEADERS, HtmlParseScraper

_cfg = load_target("sap")

if _cfg is not None:

    class SapScraper(HtmlParseScraper):
        company = "sap"
        url = _cfg["endpoint"]
        page_size = _cfg["page_size"]

        def fetch_raw(self) -> Any:
            pages = []
            startrow = 0
            params = _cfg["params"]
            jitter = _cfg["jitter_range"]
            while True:
                time.sleep(random.uniform(jitter[0], jitter[1]))
                resp = requests.get(self.url, params={
                    "q": params["q"],
                    "locationsearch": params["locationsearch"],
                    params["startrow_param"]: startrow,
                }, headers=DEFAULT_HEADERS, timeout=self.timeout)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                rows = soup.select(_cfg["selectors"]["rows"])
                if not rows:
                    break
                pages.append(rows)
                if len(rows) < self.page_size:
                    break
                startrow += self.page_size
            return pages

        def parse(self, raw: Any) -> list[JobPosting]:
            sel = _cfg["selectors"]
            url_tpl = _cfg["url_template"]
            postings = []
            for rows in raw:
                for row in rows:
                    link = row.select_one(sel["title_link"])
                    loc = row.select_one(sel["location"])
                    if not link:
                        continue
                    href = link["href"]
                    if href.startswith("/"):
                        href = url_tpl.format(href=href)
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
else:
    SCRAPER = None
