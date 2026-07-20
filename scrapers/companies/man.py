from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from ..base import JobPosting
from ..direct_json import DirectJsonScraper


class ManScraper(DirectJsonScraper):
    company = "man"
    url = "https://jobs.man.eu/services/recruiting/v1/jobs"
    method = "POST"

    def fetch_raw(self) -> Any:
        # confirmed live: pageNumber:0 alone silently truncated to 10 of
        # 23 total jobs - loop using the response's own totalJobs field
        results = []
        page_number = 0
        total = None
        while total is None or len(results) < total:
            resp = requests.post(self.url, json={
                "locale": "de_DE",
                "pageNumber": page_number,
                "sortBy": "",
                "keywords": "München",
                "location": "",
                "facetFilters": {},
            }, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            page = data.get("jobSearchResult", [])
            if not page:
                break
            results.extend(page)
            total = data.get("totalJobs", len(results))
            page_number += 1
        return {"jobSearchResult": results}

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
