from __future__ import annotations

from typing import Any

import requests
from bs4 import BeautifulSoup

from ..base import JobPosting
from ..html_parse import DEFAULT_HEADERS, HtmlParseScraper


class RohdeSchwarzScraper(HtmlParseScraper):
    company = "rohde_schwarz"
    url = "https://www.rohde-schwarz.com/us/career/jobs/career-jobboard_251573.html"
    page_size = 30

    def fetch_raw(self) -> Any:
        pages = []
        offset = 0
        while True:
            resp = requests.get(self.url, params={
                "term": "",
                "filter[rsCountry][]": "Germany",
                "filter[rsCity][]": "Munich",
                "offset": offset,
            }, headers=DEFAULT_HEADERS, timeout=self.timeout)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select(".results > .module-accordion")
            if not cards:
                break
            pages.append(cards)
            if len(cards) < self.page_size:
                break
            offset += self.page_size

        return pages

    def parse(self, raw: Any) -> list[JobPosting]:
        postings = []
        for cards in raw:
            for card in cards:
                link = card.select_one(".accordion-table-list-item-title-link")
                if not link:
                    continue
                # read by label instead of column position - the columns
                # aren't in a guaranteed fixed order
                fields = {}
                for item in card.select(".accordion-table-list-item"):
                    label = item.select_one(".accordion-table-list-item-type")
                    value = item.select_one(".accordion-table-list-item-info")
                    if label and value:
                        fields[label.get_text(strip=True)] = value.get_text(strip=True)

                href = link["href"]
                if href.startswith("/"):
                    href = f"https://www.rohde-schwarz.com{href}"
                job_id = href.rstrip("/").rsplit("-", 1)[-1].replace(".html", "")

                postings.append(JobPosting(
                    company=self.company,
                    external_id=job_id,
                    title=link.get_text(strip=True),
                    location=", ".join(filter(None, [fields.get("City/region"), fields.get("Location")])) or None,
                    url=href,
                    department=fields.get("Functional area"),
                    posted_at=None,
                ))
        return postings


SCRAPER = RohdeSchwarzScraper()
