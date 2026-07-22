from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from targets.loader import load_target

from ..base import JobPosting
from ..direct_json import DirectJsonScraper

_cfg = load_target("continental")


class ContinentalScraper(DirectJsonScraper):
    company = "continental"
    url = _cfg["endpoint"]

    def fetch_raw(self) -> Any:
        params = _cfg["params"]
        hits: list[dict] = []
        page = 1
        while True:
            resp = requests.get(self.url, params={
                "q": params["q"],
                "page": page,
                "per_page": params["per_page"],
                "locale": params["locale"],
                "filter_by": f"location:({params['latitude']}, {params['longitude']}, {params['radius']})",
            }, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            page_hits = data.get(_cfg["field_mappings"]["container"], [])
            hits.extend(page_hits)
            if not page_hits or len(hits) >= data.get(_cfg["field_mappings"]["total"], 0):
                break
            page += 1
        return hits

    def filter_location(self, postings: list[JobPosting]) -> list[JobPosting]:
        return postings

    def parse(self, raw: Any) -> list[JobPosting]:
        fm = _cfg["field_mappings"]
        url_tpl = _cfg["url_template"]
        postings = []
        for hit in raw:
            job = hit.get(fm["document_key"], {})
            posted_at = None
            if job.get(fm["date_field"]):
                try:
                    posted_at = datetime.fromisoformat(job[fm["date_field"]].replace("Z", "+00:00"))
                except ValueError:
                    pass
            path = job.get(fm["url_field"])
            postings.append(JobPosting(
                company=self.company,
                external_id=job.get(fm["ref_number"]) or job.get(fm["id_fallback"]),
                title=job.get(fm["title"], ""),
                location=", ".join(filter(None, [job.get(fm["city"]), job.get(fm["country_region"])])) or None,
                url=url_tpl.format(path=path) if path else None,
                department=job.get(fm["department"]) or None,
                posted_at=posted_at,
            ))
        return postings


SCRAPER = ContinentalScraper()
