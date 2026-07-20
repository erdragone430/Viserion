from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from .base import BaseScraper, JobPosting


class DirectJsonScraper(BaseScraper):
    """Base for scrapers backed by a single JSON HTTP endpoint."""

    url: str
    method = "GET"
    timeout = 15

    def request_kwargs(self) -> dict:
        return {}

    def fetch_raw(self) -> Any:
        resp = requests.request(self.method, self.url, timeout=self.timeout, **self.request_kwargs())
        resp.raise_for_status()
        return resp.json()


class PcsxScraper(DirectJsonScraper):
    """Shared adapter for the 'pcsx' candidate-search API (Microsoft, Infineon, ...).

    Confirmed identical path/param/response shape across companies, but the
    host differs per company (apply.careers.microsoft.com vs jobs.infineon.com),
    so both host and domain are constructor args, not just domain.
    """

    def __init__(self, company: str, host: str, domain: str, location_query: str = "Munich"):
        self.company = company
        self.host = host
        self.url = f"https://{host}/api/pcsx/search"
        self.domain = domain
        self.location_query = location_query

    def request_kwargs(self) -> dict:
        return {"params": {"domain": self.domain, "query": "", "location": self.location_query, "start": 0}}

    def parse(self, raw: Any) -> list[JobPosting]:
        postings = []
        for pos in raw.get("data", {}).get("positions", []):
            posted_at = None
            ts = pos.get("postedTs")
            if ts:
                posted_at = datetime.fromtimestamp(ts, tz=timezone.utc)
            locations = pos.get("standardizedLocations") or pos.get("locations") or []
            path = pos.get("positionUrl")
            url = f"https://{self.host}{path}" if path and path.startswith("/") else path
            postings.append(JobPosting(
                company=self.company,
                external_id=str(pos.get("atsJobId") or pos.get("id")),
                title=pos.get("name", ""),
                location=", ".join(locations) if locations else None,
                url=url,
                department=pos.get("department"),
                posted_at=posted_at,
            ))
        return postings


class GreenhouseScraper(DirectJsonScraper):
    """Generic adapter for any company on the public Greenhouse Job Board API."""

    def __init__(self, company: str, board_token: str):
        self.company = company
        self.board_token = board_token
        self.url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"

    def parse(self, raw: Any) -> list[JobPosting]:
        postings = []
        for job in raw.get("jobs", []):
            posted_at = None
            if job.get("first_published"):
                try:
                    posted_at = datetime.fromisoformat(job["first_published"])
                except ValueError:
                    pass
            postings.append(JobPosting(
                company=self.company,
                external_id=str(job["id"]),
                title=job.get("title", ""),
                location=(job.get("location") or {}).get("name"),
                url=job.get("absolute_url"),
                department=None,
                posted_at=posted_at,
            ))
        return postings
