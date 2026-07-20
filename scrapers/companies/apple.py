from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from ..base import JobPosting
from ..direct_json import DirectJsonScraper


class AppleScraper(DirectJsonScraper):
    """Needs a session cookie + CSRF token handshake before the search POST works -
    confirmed live: a cold requests.Session() (no full browser) is enough, as long
    as the handshake order (GET page -> GET CSRFToken -> POST search, cookie jar
    carried throughout) is followed.
    """

    company = "apple"
    search_url = "https://jobs.apple.com/api/v1/search"
    page_size = 20

    def fetch_raw(self) -> Any:
        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        })
        session.get("https://jobs.apple.com/en-us/search?location=munich-MUN", timeout=self.timeout)
        csrf_resp = session.get("https://jobs.apple.com/api/v1/CSRFToken", timeout=self.timeout)
        csrf_resp.raise_for_status()
        token = csrf_resp.headers["x-apple-csrf-token"]

        results = []
        page = 1
        total = None
        while total is None or len(results) < total:
            resp = session.post(self.search_url, json={
                "query": "",
                "filters": {"locations": ["postLocation-MUN"]},
                "page": page,
                "locale": "en-us",
                "sort": "",
                "format": {"longDate": "MMMM D, YYYY", "mediumDate": "MMM D, YYYY"},
            }, headers={"x-apple-csrf-token": token}, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json().get("res", {})
            batch = data.get("searchResults", [])
            if not batch:
                break
            results.extend(batch)
            total = data.get("totalRecords", len(results))
            page += 1
        return results

    def parse(self, raw: Any) -> list[JobPosting]:
        postings = []
        for job in raw:
            posted_at = None
            if job.get("postDateInGMT"):
                try:
                    posted_at = datetime.fromisoformat(job["postDateInGMT"].replace("Z", "+00:00"))
                except ValueError:
                    pass
            locations = job.get("locations") or []
            position_id = job.get("positionId")
            slug = job.get("transformedPostingTitle")
            url = f"https://jobs.apple.com/en-us/details/{position_id}/{slug}" if position_id and slug else None
            postings.append(JobPosting(
                company=self.company,
                external_id=job.get("jobPositionId") or job.get("id") or position_id,
                title=job.get("postingTitle", ""),
                location=", ".join(loc.get("name", "") for loc in locations if loc.get("name")) or None,
                url=url,
                department=(job.get("team") or {}).get("teamName"),
                posted_at=posted_at,
            ))
        return postings


SCRAPER = AppleScraper()
