from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from ..base import JobPosting
from ..html_parse import HtmlParseScraper


class FlixBusScraper(HtmlParseScraper):
    company = "flixbus"
    url = "https://flix.careers/locations/munich/"  # already server-filtered to Munich

    def parse(self, raw: Any) -> list[JobPosting]:
        soup = BeautifulSoup(raw, "html.parser")
        postings = []
        for a in soup.select(".jobs .card a"):
            href = a["href"]
            if href.startswith("/"):
                href = f"https://flix.careers{href}"
            title_el = a.select_one("h6")
            location_el = a.select_one(".location")
            job_id = href.split("jobid=")[-1].split("&")[0] if "jobid=" in href else href
            postings.append(JobPosting(
                company=self.company,
                external_id=job_id,
                title=title_el.get_text(strip=True) if title_el else "",
                location=location_el.get_text(strip=True) if location_el else "Munich",
                url=href,
                department=None,
                posted_at=None,
            ))
        return postings


SCRAPER = FlixBusScraper()
