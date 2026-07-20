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

    def fetch_raw(self) -> Any:
        # confirmed live: page size is server-set (10/page) and `start:0`
        # alone silently truncated Infineon to 10 of 93 total positions -
        # loop on the response's own `count` until we've collected them all
        positions = []
        total = None
        while total is None or len(positions) < total:
            resp = requests.get(self.url, params={
                "domain": self.domain, "query": "", "location": self.location_query, "start": len(positions),
            }, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            page = data.get("positions", [])
            if not page:
                break
            positions.extend(page)
            total = data.get("count", len(positions))
        return {"data": {"positions": positions}}

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


class WorkdayScraper(DirectJsonScraper):
    """Generic adapter for any company on a Workday-hosted candidate site (CxS API).

    Confirmed against Airbus (ag.wd3.myworkdayjobs.com/wday/cxs/ag/Airbus/jobs).
    host/tenant/site are constructor args since they vary per company; applied_facets
    lets a company scope server-side to a division/legal-entity and/or location facet
    IDs (reverse-engineered from the site's own search UI, not guessed).
    """

    method = "POST"
    page_size = 20

    def __init__(self, company: str, host: str, tenant: str, site: str, applied_facets: dict | None = None):
        self.company = company
        self.host = host
        self.tenant = tenant
        self.site = site
        self.url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
        self.applied_facets = applied_facets or {}

    def fetch_raw(self) -> Any:
        # confirmed live: Workday's `total` field is only populated on the
        # very first offset=0 response - every later page reports total:0,
        # which made the old `offset >= total` check stop after page 2
        # (40/67 Airbus postings). Stop on a short page instead, same
        # pattern as Amazon/Apple's pagination.
        postings = []
        offset = 0
        while True:
            resp = requests.post(self.url, json={
                "appliedFacets": self.applied_facets,
                "limit": self.page_size,
                "offset": offset,
                "searchText": "",
            }, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            page = data.get("jobPostings", [])
            postings.extend(page)
            if len(page) < self.page_size:
                break
            offset += self.page_size
        return postings

    def filter_location(self, postings):
        # applied_facets already scope results to exact location facet IDs
        # reverse-engineered from the site's own search UI (see the
        # docstring above) - that's a precise server-side filter, not a
        # fuzzy one, so the usual text re-check would only hurt here.
        # Confirmed live: 12/67 Airbus postings have ambiguous display
        # text ("2 Locations" etc., incl. facet-confirmed Taufkirchen/
        # Ottobrunn jobs) that the default text match would wrongly drop.
        return postings

    def parse(self, raw: Any) -> list[JobPosting]:
        postings = []
        for job in raw:
            path = job.get("externalPath")
            postings.append(JobPosting(
                company=self.company,
                external_id=path or job.get("title", ""),
                title=job.get("title", ""),
                location=job.get("locationsText"),
                url=f"https://{self.host}/en-US/{self.site}{path}" if path else None,
                department=None,
                posted_at=None,
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
