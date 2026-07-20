from __future__ import annotations

from datetime import datetime
from typing import Any

from ..base import JobPosting
from ..direct_json import DirectJsonScraper


class ManScraper(DirectJsonScraper):
    company = "man"
    url = "https://jobs.man.eu/services/recruiting/v1/jobs"
    method = "POST"

    def request_kwargs(self) -> dict:
        return {"json": {
            "locale": "de_DE",
            "pageNumber": 0,
            "sortBy": "",
            "keywords": "München",
            "location": "",
            "facetFilters": {},
        }}

    def parse(self, raw: Any) -> list[JobPosting]:
        postings = []
        for entry in raw.get("jobSearchResult", []):
            pos = entry.get("response", entry)
            job_id = pos.get("id")
            slug = pos.get("urlTitle")
            # filter7/filter1 are single-element lists in the live response
            city = (pos.get("filter7") or [None])[0]
            department = (pos.get("filter1") or [None])[0]
            posted_at = None
            date_str = pos.get("unifiedStandardStart")
            if date_str:
                try:
                    posted_at = datetime.strptime(date_str, "%d.%m.%y")
                except ValueError:
                    pass
            postings.append(JobPosting(
                company=self.company,
                external_id=str(job_id),
                title=pos.get("unifiedStandardTitle", ""),
                # feeding the precise filter7 city into `location` means the
                # standard filter_location() re-check against it doubles as
                # the client-side precision re-validation the recon flagged
                location=city,
                url=f"https://jobs.man.eu/job/{slug}/{job_id}-de_DE" if slug and job_id else None,
                department=department,
                posted_at=posted_at,
            ))
        return postings


SCRAPER = ManScraper()
