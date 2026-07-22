from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from targets.loader import load_target

from ..base import JobPosting
from ..direct_json import DirectJsonScraper

_cfg = load_target("apple")


class AppleScraper(DirectJsonScraper):
    company = "apple"
    url = _cfg["endpoints"]["search"]
    search_url = _cfg["endpoints"]["search"]
    page_size = _cfg["page_size"]

    def fetch_raw(self) -> Any:
        eps = _cfg["endpoints"]
        ua = _cfg["user_agent"]
        csrf_header = _cfg["csrf_header"]
        sp = _cfg["search_payload"]

        session = requests.Session()
        session.headers.update({"User-Agent": ua})
        session.get(eps["cookie_page"], timeout=self.timeout)
        csrf_resp = session.get(eps["csrf_token"], timeout=self.timeout)
        csrf_resp.raise_for_status()
        token = csrf_resp.headers[csrf_header]

        fm = _cfg["field_mappings"]
        results = []
        page = 1
        total = None
        while total is None or len(results) < total:
            resp = session.post(self.search_url, json={
                "query": "",
                "filters": {"locations": sp["locations"]},
                "page": page,
                "locale": sp["locale"],
                "sort": "",
                "format": {"longDate": sp["long_date_format"], "mediumDate": sp["medium_date_format"]},
            }, headers={csrf_header: token}, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json().get(fm["response_container"], {})
            batch = data.get(fm["results_container"], [])
            if not batch:
                break
            results.extend(batch)
            total = data.get(fm["total_records"], len(results))
            page += 1
        return results

    def parse(self, raw: Any) -> list[JobPosting]:
        fm = _cfg["field_mappings"]
        url_tpl = _cfg["url_template"]
        postings = []
        for job in raw:
            posted_at = None
            if job.get(fm["posted_date"]):
                try:
                    posted_at = datetime.fromisoformat(job[fm["posted_date"]].replace("Z", "+00:00"))
                except ValueError:
                    pass
            locations = job.get(fm["locations"]) or []
            position_id = job.get(fm["position_id"])
            slug = job.get(fm["slug"])
            url = url_tpl.format(position_id=position_id, slug=slug) if position_id and slug else None
            postings.append(JobPosting(
                company=self.company,
                external_id=job.get(fm["job_position_id"]) or job.get(fm["id_fallback"]) or position_id,
                title=job.get(fm["posting_title"], ""),
                location=", ".join(loc.get(fm["location_name"], "") for loc in locations if loc.get(fm["location_name"])) or None,
                url=url,
                department=(job.get(fm["team_container"]) or {}).get(fm["team_name"]),
                posted_at=posted_at,
            ))
        return postings


SCRAPER = AppleScraper()
