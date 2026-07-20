from __future__ import annotations

from datetime import datetime
from typing import Any

from ..base import JobPosting
from ..direct_json import DirectJsonScraper


class PersonioScraper(DirectJsonScraper):
    company = "personio"
    url = "https://www.personio.com/api/careers/jobs/list/"

    def parse(self, raw: Any) -> list[JobPosting]:
        postings = []
        for job in raw:
            posted_at = None
            if job.get("createdAt"):
                try:
                    posted_at = datetime.strptime(job["createdAt"], "%Y-%m-%d")
                except ValueError:
                    pass
            postings.append(JobPosting(
                company=self.company,
                external_id=job["id"],
                title=job.get("name", ""),
                location=", ".join(job.get("allOffices") or []),
                url=f"https://www.personio.com/careers/{job['id']}/",
                department=job.get("department"),
                posted_at=posted_at,
            ))
        return postings


SCRAPER = PersonioScraper()
