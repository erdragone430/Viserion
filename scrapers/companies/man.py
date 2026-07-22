from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from targets.loader import load_target

from ..base import JobPosting
from ..direct_json import DirectJsonScraper

_cfg = load_target("man")

if _cfg is not None:

    class ManScraper(DirectJsonScraper):
        company = "man"
        url = _cfg["endpoint"]
        method = _cfg.get("method", "POST")

        def fetch_raw(self) -> Any:
            results = []
            page_number = 0
            total = None
            while total is None or len(results) < total:
                body = dict(_cfg["request_payload"])
                body["pageNumber"] = page_number
                resp = requests.post(self.url, json=body, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
                page = data.get(_cfg["field_mappings"]["container"], [])
                if not page:
                    break
                results.extend(page)
                total = data.get(_cfg["field_mappings"]["total"], len(results))
                page_number += 1
            return {_cfg["field_mappings"]["container"]: results}

        def parse(self, raw: Any) -> list[JobPosting]:
            fm = _cfg["field_mappings"]
            date_fmt = _cfg["date_format"]
            url_tpl = _cfg["url_template"]
            postings = []
            for entry in raw.get(fm["container"], []):
                pos = entry.get(fm["nested_entry"], entry)
                job_id = pos.get(fm["id"])
                slug = pos.get(fm["slug"])
                city_list = pos.get(fm["city_field"]) or [None]
                dept_list = pos.get(fm["department_field"]) or [None]
                posted_at = None
                date_str = pos.get(fm["date_field"])
                if date_str:
                    try:
                        posted_at = datetime.strptime(date_str, date_fmt)
                    except ValueError:
                        pass
                postings.append(JobPosting(
                    company=self.company,
                    external_id=str(job_id),
                    title=pos.get(fm["title_field"], ""),
                    location=city_list[0],
                    url=url_tpl.format(slug=slug, job_id=job_id) if slug and job_id else None,
                    department=dept_list[0],
                    posted_at=posted_at,
                ))
            return postings

    SCRAPER = ManScraper()
else:
    SCRAPER = None
