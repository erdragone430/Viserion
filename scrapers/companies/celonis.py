from __future__ import annotations

from datetime import datetime
from typing import Any

from ..base import JobPosting
from ..direct_json import DirectJsonScraper


class CelonisScraper(DirectJsonScraper):
    company = "celonis"
    url = "https://dxp-api.celonis.com/v1/jobs"

    def parse(self, raw: Any) -> list[JobPosting]:
        postings = []
        for job in raw.get("jobs", []):
            posted_at = None
            if job.get("updatedAt"):
                try:
                    posted_at = datetime.fromisoformat(job["updatedAt"])
                except ValueError:
                    pass
            postings.append(JobPosting(
                company=self.company,
                external_id=str(job["jobId"]),
                title=job.get("title", ""),
                location=job.get("groupedLocation"),
                url=f"https://careers.celonis.com/join-us/open-positions/job-detail?jobId={job['jobId']}",
                department=job.get("team"),
                posted_at=posted_at,
            ))
        return postings


SCRAPER = CelonisScraper()
