from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

import requests

from targets.loader import load_target

from ..base import JobPosting
from ..html_parse import DEFAULT_HEADERS, HtmlParseScraper

_cfg = load_target("google")

if _cfg is not None:
    AF_CALLBACK_RE = re.compile(_cfg["callback_regex"])

    class GoogleScraper(HtmlParseScraper):
        company = "google"
        url = _cfg["endpoint"]

        def fetch_raw(self) -> Any:
            pages = []
            page = 1
            total = None
            params = _cfg["params"]
            while total is None or len(pages) < total:
                resp = requests.get(self.url, params={
                    params["page_param"]: page,
                    "location": params["location"],
                }, headers=DEFAULT_HEADERS, timeout=self.timeout)
                resp.raise_for_status()
                jobs, total = self._extract_jobs(resp.text)
                if not jobs:
                    break
                pages.extend(jobs)
                page += 1
            return pages

        @staticmethod
        def _extract_jobs(html: str) -> tuple[list, int]:
            idx = _cfg["indices"]
            for _key, data_str in AF_CALLBACK_RE.findall(html):
                try:
                    data = json.loads(data_str)
                except (json.JSONDecodeError, ValueError):
                    continue
                if not (isinstance(data, list) and data and isinstance(data[0], list) and data[0]):
                    continue
                first = data[idx["first_entry"]][idx["first_inner_entry"]]
                if isinstance(first, list) and len(first) > 10 and isinstance(first[1], str):
                    total = data[idx["data_total"]] if len(data) > idx["data_total"] and isinstance(data[idx["data_total"]], int) else len(data[0])
                    return data[0], total
            return [], 0

        def parse(self, raw: Any) -> list[JobPosting]:
            idx = _cfg["indices"]
            url_tpl = _cfg["url_template"]
            postings = []
            for job in raw:
                job_id = job[idx["job_id"]]
                title = job[idx["title"]]
                locations = job[idx["locations"]] or []
                posted_ts = job[idx["posted_ts_array"]][idx["posted_ts_value"]] if job[idx["posted_ts_array"]] else None
                posted_at = datetime.fromtimestamp(posted_ts, tz=timezone.utc) if posted_ts else None
                postings.append(JobPosting(
                    company=self.company,
                    external_id=str(job_id),
                    title=title,
                    location=", ".join(loc[idx["location_display_name"]] for loc in locations) or None,
                    url=url_tpl.format(job_id=job_id),
                    department=None,
                    posted_at=posted_at,
                ))
            return postings

    SCRAPER = GoogleScraper()
else:
    SCRAPER = None
