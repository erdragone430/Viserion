from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from ..base import JobPosting
from ..direct_json import DirectJsonScraper

# Continental moved to a new careers platform (jobs.continental-industry.com)
# in mid-2026; the old tx_conjobs_api endpoint is gone. Same static Munich
# coordinates as before - see git history for the prior platform's version.
MUNICH_LAT = 48.1391
MUNICH_LON = 11.5802


class ContinentalScraper(DirectJsonScraper):
    company = "continental"
    url = "https://5aexd5th6e.execute-api.eu-central-1.amazonaws.com/v1/jobs/search"

    def fetch_raw(self) -> Any:
        # Confirmed live: this Typesense-backed API caps per_page at 50
        # no matter what's requested, and `found` stays accurate on every
        # page (unlike Workday's offset bug) - loop on it directly.
        hits: list[dict] = []
        page = 1
        while True:
            resp = requests.get(self.url, params={
                "q": "*",
                "page": page,
                "per_page": 50,
                "locale": "en",
                # Site's own default radius (50km). Confirmed live: 50/100/150km
                # all return 0 around Munich; first hit appears only at 300km
                # (Herbolzheim/Weißbach) - same "don't widen" call as before.
                "filter_by": f"location:({MUNICH_LAT}, {MUNICH_LON}, 50 km)",
            }, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            page_hits = data.get("hits", [])
            hits.extend(page_hits)
            if not page_hits or len(hits) >= data.get("found", 0):
                break
            page += 1
        return hits

    def parse(self, raw: Any) -> list[JobPosting]:
        postings = []
        for hit in raw:
            job = hit.get("document", {})
            posted_at = None
            if job.get("postedAt"):
                try:
                    posted_at = datetime.fromisoformat(job["postedAt"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            path = job.get("url")
            postings.append(JobPosting(
                company=self.company,
                external_id=job.get("refNumber") or job.get("id"),
                title=job.get("name", ""),
                location=", ".join(filter(None, [job.get("city"), job.get("countryRegion")])) or None,
                url=f"https://jobs.continental-industry.com{path}" if path else None,
                department=job.get("fieldOfWork") or None,
                posted_at=posted_at,
            ))
        return postings

    def filter_location(self, postings: list[JobPosting]) -> list[JobPosting]:
        # filter_by=location:(...) above already does exact server-side
        # geo-radius filtering (confirmed live) - same override rationale as
        # WorkdayScraper/Siemens: a text re-check would only risk dropping
        # postings whose city/countryRegion text doesn't literally say Munich.
        return postings


SCRAPER = ContinentalScraper()
