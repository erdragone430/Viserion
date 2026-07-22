from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from targets.loader import load_target

from ..base import JobPosting
from ..direct_json import DirectJsonScraper

_cfg = load_target("amazon")

if _cfg is not None:

    class AmazonScraper(DirectJsonScraper):
        company = "amazon"
        url = _cfg["endpoint"]
        page_size = _cfg["page_size"]

        def fetch_raw(self) -> Any:
            params = _cfg["params"]
            jobs = []
            offset = 0
            while True:
                resp = requests.get(self.url, params={
                    "latitude": params["latitude"],
                    "longitude": params["longitude"],
                    "radius": params["radius"],
                    "result_limit": self.page_size,
                    "offset": offset,
                }, timeout=self.timeout)
                resp.raise_for_status()
                page = resp.json().get(_cfg["field_mappings"]["container"]) or []
                jobs.extend(page)
                if len(page) < self.page_size:
                    break
                offset += self.page_size
            return jobs

        def parse(self, raw: Any) -> list[JobPosting]:
            fm = _cfg["field_mappings"]
            date_fmt = _cfg["date_format"]
            url_tpl = _cfg["url_template"]
            postings = []
            for job in raw:
                posted_at = None
                date_str = job.get(fm["posted_date"])
                if date_str:
                    try:
                        posted_at = datetime.strptime(date_str, date_fmt)
                    except ValueError:
                        pass
                job_path = job.get(fm["job_path"])
                postings.append(JobPosting(
                    company=self.company,
                    external_id=str(job.get(fm["id_icims"]) or job.get(fm["id_fallback"])),
                    title=job.get(fm["title"], ""),
                    location=job.get(fm["location"]) or job.get(fm["location_fallback"]),
                    url=f"{url_tpl}{job_path}" if job_path else None,
                    department=job.get(fm["department"]),
                    posted_at=posted_at,
                ))
            return postings

    SCRAPER = AmazonScraper()
else:
    SCRAPER = None
