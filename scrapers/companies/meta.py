from __future__ import annotations

import logging
import time
from typing import Any

from playwright.sync_api import sync_playwright

from ..base import BaseScraper, JobPosting

logger = logging.getLogger(__name__)

RESPONSE_TIMEOUT_MS = 30_000


class MetaScraper(BaseScraper):
    """Needs a real headless browser (not just realistic headers) - confirmed
    live that a plain `requests` call intermittently gets a WAF error page
    even with a full browser User-Agent.

    Rather than manually reconstructing the GraphQL call (hardcoded doc_id +
    scraped x-fb-lsd token), we let the real page make its own request and
    intercept the response. This avoids depending on Meta's persisted-query
    scheme, which changes silently across frontend builds.
    """

    company = "meta"

    def fetch_raw(self) -> Any:
        start = time.monotonic()
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page()
                # Diagnostic only - logs every graphql response seen (matched or
                # not) so a timeout failure in prod shows what actually arrived,
                # instead of just "nothing matched within 30s".
                page.on("response", lambda r: self._log_graphql_response(r, start))
                with page.expect_response(
                    self._is_job_search_response, timeout=RESPONSE_TIMEOUT_MS
                ) as response_info:
                    page.goto("https://www.metacareers.com/jobs", wait_until="domcontentloaded")
                result = response_info.value.json()
                logger.info("meta: matched all_jobs response at +%.2fs", time.monotonic() - start)
            finally:
                browser.close()
        return result

    @staticmethod
    def _log_graphql_response(response, start: float) -> None:
        if "metacareers.com/graphql" not in response.url:
            return
        try:
            body = response.json()
            keys = list((body.get("data") or {}).keys())
            snippet = f"data keys={keys}"
        except Exception as exc:
            snippet = f"<unparseable: {exc}>"
        logger.info("meta: graphql response at +%.2fs status=%s %s", time.monotonic() - start, response.status, snippet)

    @staticmethod
    def _is_job_search_response(response) -> bool:
        if "metacareers.com/graphql" not in response.url:
            return False
        try:
            body = response.json()
        except Exception:
            return False
        return "all_jobs" in (body.get("data", {}).get("job_search_with_featured_jobs_v2", {}) or {})

    def parse(self, raw: Any) -> list[JobPosting]:
        jobs = raw.get("data", {}).get("job_search_with_featured_jobs_v2", {}).get("all_jobs", []) or []
        postings = []
        for job in jobs:
            postings.append(JobPosting(
                company=self.company,
                external_id=str(job["id"]),
                title=job.get("title", ""),
                location=", ".join(job.get("locations") or []) or None,
                url=f"https://www.metacareers.com/profile/job_details/{job['id']}/",
                department=", ".join(job.get("teams") or []) or None,
                posted_at=None,
            ))
        return postings


SCRAPER = MetaScraper()
