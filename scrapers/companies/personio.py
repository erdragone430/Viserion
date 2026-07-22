from __future__ import annotations

from datetime import datetime
from typing import Any

from targets.loader import load_target

from ..base import JobPosting
from ..direct_json import DirectJsonScraper

_cfg = load_target("personio")

if _cfg is not None:

    class PersonioScraper(DirectJsonScraper):
        company = "personio"
        url = _cfg["endpoint"]

        def parse(self, raw: Any) -> list[JobPosting]:
            fm = _cfg["field_mappings"]
            url_tpl = _cfg["url_template"]
            date_fmt = _cfg["date_format"]
            postings = []
            for job in raw:
                posted_at = None
                date_str = job.get(fm["date_field"])
                if date_str:
                    try:
                        posted_at = datetime.strptime(date_str, date_fmt)
                    except ValueError:
                        pass
                job_id = job[fm["id"]]
                postings.append(JobPosting(
                    company=self.company,
                    external_id=job_id,
                    title=job.get(fm["title"], ""),
                    location=", ".join(job.get(fm["offices"]) or []),
                    url=url_tpl.format(job_id=job_id),
                    department=job.get(fm["department"]),
                    posted_at=posted_at,
                ))
            return postings

    SCRAPER = PersonioScraper()
else:
    SCRAPER = None
