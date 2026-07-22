from __future__ import annotations

from datetime import datetime
from typing import Any

from targets.loader import load_target

from ..base import JobPosting
from ..direct_json import DirectJsonScraper

_cfg = load_target("celonis")


class CelonisScraper(DirectJsonScraper):
    company = "celonis"
    url = _cfg["endpoint"]

    def parse(self, raw: Any) -> list[JobPosting]:
        fm = _cfg["field_mappings"]
        url_tpl = _cfg["url_template"]
        postings = []
        for job in raw.get(fm["container"], []):
            posted_at = None
            date_str = job.get(fm["date_field"])
            if date_str:
                try:
                    posted_at = datetime.fromisoformat(date_str)
                except ValueError:
                    pass
            job_id = job[fm["id"]]
            postings.append(JobPosting(
                company=self.company,
                external_id=str(job_id),
                title=job.get(fm["title"], ""),
                location=job.get(fm["location"]),
                url=url_tpl.format(job_id=job_id),
                department=job.get(fm["department"]),
                posted_at=posted_at,
            ))
        return postings


SCRAPER = CelonisScraper()
