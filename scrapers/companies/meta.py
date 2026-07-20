from __future__ import annotations

import re
from typing import Any

from playwright.sync_api import sync_playwright

from ..base import BaseScraper, JobPosting

# Relay doc_id for the "CareersJobSearchResultsV2DataQuery" persisted query -
# reverse-engineered live from metacareers.com's own network traffic, tied to
# a specific frontend build. This is the single most fragile part of this
# scraper (flagged in recon as the most fragile integration of the whole
# project): if Meta ships a new frontend build, this ID rotates and every
# call starts failing outright (not silently returning wrong data), which
# the standard scraper_health consecutive-failure alert will catch same as
# any other broken scraper - re-extract a fresh doc_id from a live page's
# network tab (x-fb-friendly-name: CareersJobSearchResultsV2DataQuery) if so.
DOC_ID = "27129360303422352"


class MetaScraper(BaseScraper):
    """Needs a real headless browser (not just realistic headers) - confirmed
    live that a plain `requests` call intermittently gets a WAF error page
    even with a full browser User-Agent, so the lsd token bootstrap runs
    inside actual Chromium and the GraphQL call itself is issued from within
    the page via fetch() to inherit its cookies/session/fingerprint.
    """

    company = "meta"

    def fetch_raw(self) -> Any:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page()
                page.goto("https://www.metacareers.com/jobsearch/", wait_until="domcontentloaded")
                match = re.search(r'"LSD",\[\],\{"token":"([^"]+)"', page.content())
                if not match:
                    raise RuntimeError("could not find lsd token on Meta careers page - frontend may have changed")
                lsd = match.group(1)

                result = page.evaluate(
                    """
                    async ({lsd, docId}) => {
                        const resp = await fetch('https://www.metacareers.com/graphql', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded',
                                'x-fb-lsd': lsd,
                            },
                            body: new URLSearchParams({
                                fb_api_caller_class: 'RelayModern',
                                fb_api_req_friendly_name: 'CareersJobSearchResultsV2DataQuery',
                                variables: JSON.stringify({
                                    search_input: {
                                        q: null, divisions: [], offices: ['Munich, Germany'], roles: [],
                                        leadership_levels: [], saved_jobs: [], saved_searches: [], sub_teams: [],
                                        teams: [], is_leadership: false, is_remote_only: false, sort_by_new: false,
                                        results_per_page: null,
                                    },
                                    viewasUserID: null, isLoggedIn: false,
                                }),
                                doc_id: docId,
                            }),
                        });
                        return await resp.json();
                    }
                    """,
                    {"lsd": lsd, "docId": DOC_ID},
                )
            finally:
                browser.close()
        return result

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
