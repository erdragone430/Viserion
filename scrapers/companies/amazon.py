from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from ..base import JobPosting
from ..direct_json import DirectJsonScraper

# ponytail: Munich's coordinates don't move; a live geocode call (+ cache) for
# one static city is more moving parts than the constant it would produce.
MUNICH_LAT = 48.1351
MUNICH_LON = 11.5820


class AmazonScraper(DirectJsonScraper):
    company = "amazon"
    url = "https://www.amazon.jobs/en/search.json"
    page_size = 100  # confirmed max accepted by result_limit; paginate via offset

    def fetch_raw(self) -> Any:
        jobs = []
        offset = 0
        while True:
            resp = requests.get(self.url, params={
                "latitude": MUNICH_LAT,
                "longitude": MUNICH_LON,
                "radius": "50mi",
                "result_limit": self.page_size,
                "offset": offset,
            }, timeout=self.timeout)
            resp.raise_for_status()
            page = resp.json().get("jobs") or []
            jobs.extend(page)
            if len(page) < self.page_size:
                break
            offset += self.page_size
        return jobs

    def parse(self, raw: Any) -> list[JobPosting]:
        postings = []
        for job in raw:
            posted_at = None
            date_str = job.get("posted_date")
            if date_str:
                try:
                    posted_at = datetime.strptime(date_str, "%B %d, %Y")
                except ValueError:
                    pass
            postings.append(JobPosting(
                company=self.company,
                external_id=str(job.get("id_icims") or job.get("id")),
                title=job.get("title", ""),
                location=job.get("normalized_location") or job.get("location"),
                url=f"https://www.amazon.jobs{job['job_path']}" if job.get("job_path") else None,
                department=job.get("job_category"),
                posted_at=posted_at,
            ))
        return postings


SCRAPER = AmazonScraper()
