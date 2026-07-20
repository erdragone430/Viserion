from __future__ import annotations

from typing import Any

import requests
from bs4 import BeautifulSoup

from ..base import JobPosting
from ..html_parse import DEFAULT_HEADERS, HtmlParseScraper


class SiemensScraper(HtmlParseScraper):
    company = "siemens"
    # Avature facet IDs (Country=Germany, State=Bavaria, City=Munich) —
    # reverse-engineered live by applying the three filters in the actual
    # search UI and capturing the resulting request, not guessed. This
    # replaces the old country-facet + free-text "/Munich/" keyword path,
    # which matched only 112/140 postings the exact facet combo returns.
    base_url = "https://jobs.siemens.com/en_US/externaljobs/SearchJobs/"
    facets = {
        "42386": "[812132]", "42386_format": "17546",  # Country: Germany
        "42387": "[813141]", "42387_format": "17547",  # State: Bavaria
        "42388": "[912803]", "42388_format": "17879",  # City: Munich
    }
    page_size = 6  # server-enforced, ignores a larger folderRecordsPerPage

    def fetch_raw(self) -> Any:
        pages = []
        offset = 0
        while True:
            resp = requests.get(self.base_url, params={
                **self.facets,
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

    def filter_location(self, postings):
        # The three facets above already do exact location-ID filtering on
        # Avature's side (confirmed live: 140/140 matches the site's own
        # "140 results" count for this filter combo) - more precise than
        # the fuzzy text re-check, and it wrongly drops "Multiple Locations"
        # postings that the facet itself already confirmed are Munich-scoped.
        return postings

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
                if city:
                    location = ", ".join(filter(None, [
                        city.get_text(strip=True),
                        state.get_text(strip=True) if state else None,
                        country.get_text(strip=True) if country else None,
                    ])) or None
                else:
                    # multi-location postings render as a single "Multiple
                    # Locations" span instead of the city/state/country
                    # breakdown - confirmed live, still true after the
                    # facet-based rewrite. filter_location() no-ops now (the
                    # City facet already guarantees relevance) so this is
                    # just for a readable `location` value, not filtering.
                    loc_el = art.select_one(".list-item-location")
                    location = loc_el.get_text(strip=True) if loc_el else None
                family = art.select_one(".list-item-family")
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
