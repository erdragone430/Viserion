from __future__ import annotations

import logging
import time
from typing import Any

from playwright.sync_api import sync_playwright

from targets.loader import load_target

from ..base import BaseScraper, JobPosting

_cfg = load_target("meta")
logger = logging.getLogger(__name__)


class MetaScraper(BaseScraper):
    company = "meta"
    RESPONSE_TIMEOUT_MS = _cfg["response_timeout_ms"]

    def fetch_raw(self) -> Any:
        start = time.monotonic()
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page()
                page.on("response", lambda r: self._log_graphql_response(r, start))
                with page.expect_response(
                    self._is_job_search_response, timeout=self.RESPONSE_TIMEOUT_MS
                ) as response_info:
                    page.goto(_cfg["page_url"], wait_until="domcontentloaded")
                result = response_info.value.json()
                logger.info("meta: matched all_jobs response at +%.2fs", time.monotonic() - start)
            finally:
                browser.close()
        return result

    @staticmethod
    def _log_graphql_response(response, start: float) -> None:
        if _cfg["graphql_url_pattern"] not in response.url:
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
        if _cfg["graphql_url_pattern"] not in response.url:
            return False
        try:
            body = response.json()
        except Exception:
            return False
        data_path = _cfg["data_path"]
        return "all_jobs" in (body.get(data_path[0], {}).get(data_path[1], {}) or {})

    def parse(self, raw: Any) -> list[JobPosting]:
        data_path = _cfg["data_path"]
        fm = _cfg["field_mappings"]
        url_tpl = _cfg["url_template"]
        jobs = raw
        for key in data_path:
            jobs = jobs.get(key, {}) if isinstance(jobs, dict) else {}
        jobs = jobs if isinstance(jobs, list) else []
        postings = []
        for job in jobs:
            postings.append(JobPosting(
                company=self.company,
                external_id=str(job[fm["id"]]),
                title=job.get(fm["title"], ""),
                location=", ".join(job.get(fm["locations"]) or []) or None,
                url=url_tpl.format(job_id=job[fm["id"]]),
                department=", ".join(job.get(fm["teams"]) or []) or None,
                posted_at=None,
            ))
        return postings


SCRAPER = MetaScraper()
