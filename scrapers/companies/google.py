from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

import requests

from ..base import JobPosting
from ..html_parse import DEFAULT_HEADERS, HtmlParseScraper

# Google's careers search results aren't in plain HTML - they're embedded as
# a Closure AF_initDataCallback(...) JS blob. Don't hardcode which ds:N key
# holds the jobs (that's an implementation detail that can shift); instead
# scan every AF_initDataCallback blob on the page and duck-type the one whose
# shape looks like a job list.
AF_CALLBACK_RE = re.compile(r"AF_initDataCallback\(\{key: '(ds:\d+)', hash: '\d+', data:(.*?), sideChannel:", re.DOTALL)


class GoogleScraper(HtmlParseScraper):
    company = "google"
    url = "https://www.google.com/about/careers/applications/jobs/results/"

    def fetch_raw(self) -> Any:
        pages = []
        page = 1
        total = None
        while total is None or len(pages) < total:
            resp = requests.get(self.url, params={
                "location": "Munich, Germany",
                "page": page,
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
        for _key, data_str in AF_CALLBACK_RE.findall(html):
            try:
                data = json.loads(data_str)
            except (json.JSONDecodeError, ValueError):
                continue
            if not (isinstance(data, list) and data and isinstance(data[0], list) and data[0]):
                continue
            first = data[0][0]
            if isinstance(first, list) and len(first) > 10 and isinstance(first[1], str):
                total = data[2] if len(data) > 2 and isinstance(data[2], int) else len(data[0])
                return data[0], total
        return [], 0

    def parse(self, raw: Any) -> list[JobPosting]:
        postings = []
        for job in raw:
            # Positional indices reverse-engineered on 2026-07-20 by
            # cross-referencing this blob against the rendered page for
            # known jobs. There are no field names in this payload - this
            # is the single most fragile part of the project; if Google
            # changes their frontend, re-verify these offsets first.
            job_id = job[0]                                     # [0]  numeric job id (string)
            title = job[1]                                      # [1]  job title
            locations = job[9] or []                            # [9]  [[displayName, [aliases], city, null, region, countryCode], ...]
            posted_ts = job[12][0] if job[12] else None          # [12] [unix_seconds, nanos] - first-published timestamp

            posted_at = datetime.fromtimestamp(posted_ts, tz=timezone.utc) if posted_ts else None
            postings.append(JobPosting(
                company=self.company,
                external_id=str(job_id),
                title=title,
                location=", ".join(loc[0] for loc in locations) or None,
                # bare numeric-id URL confirmed to resolve (200) without
                # needing the title slug Google appends for humans
                url=f"https://www.google.com/about/careers/applications/jobs/results/{job_id}",
                department=None,
                posted_at=posted_at,
            ))
        return postings


SCRAPER = GoogleScraper()
