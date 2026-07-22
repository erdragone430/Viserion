from __future__ import annotations

from typing import Any

from targets.loader import load_target

from ..base import JobPosting
from ..direct_json import DirectJsonScraper

_cfg = load_target("ibm")

if _cfg is not None:

    class IbmScraper(DirectJsonScraper):
        company = "ibm"
        url = _cfg["endpoint"]
        method = _cfg.get("method", "POST")

        def request_kwargs(self) -> dict:
            payload = dict(_cfg["request_payload"])
            return {"json": {
                "appId": payload["appId"],
                "scopes": payload["scopes"],
                "query": {"bool": {"must": []}},
                "post_filter": {"term": {payload["country_filter_field"]: payload["country_filter_value"]}},
                "size": payload["size"],
                "from": payload["from"],
                "sort": payload["sort"],
                "lang": payload["lang"],
                "localeSelector": payload.get("localeSelector", {}),
                "sm": payload.get("sm", {}),
                "_source": payload.get("_source", []),
            }}

        def parse(self, raw: Any) -> list[JobPosting]:
            fm = _cfg["field_mappings"]
            postings = []
            for hit in raw.get(fm["hits_outer"], {}).get(fm["hits_inner"], []):
                src = hit.get(fm["source"], {})
                postings.append(JobPosting(
                    company=self.company,
                    external_id=hit.get(fm["id"]) or src.get(fm["url"], ""),
                    title=src.get(fm["title"], ""),
                    location=src.get(fm["city"]),
                    url=src.get(fm["url"]),
                    department=src.get(fm["department"]),
                    posted_at=None,
                ))
            return postings

    SCRAPER = IbmScraper()
else:
    SCRAPER = None
