from __future__ import annotations

from typing import Any

from ..base import JobPosting
from ..direct_json import DirectJsonScraper


class IbmScraper(DirectJsonScraper):
    """Scoped to IBM's German listings, not IBM globally (per request).

    No city-level facet exists on this API - only a country facet
    (field_keyword_05) - so "Germany" is the server-side filter and the
    Munich narrowing happens client-side via the standard filter_location()
    check against field_keyword_19 (the city field).
    """

    company = "ibm"
    url = "https://www-api.ibm.com/search/api/v2"
    method = "POST"

    def request_kwargs(self) -> dict:
        return {"json": {
            "appId": "careers",
            "scopes": ["careers2"],
            "query": {"bool": {"must": []}},
            "post_filter": {"term": {"field_keyword_05": "Germany"}},
            # ponytail: single page covers it - Germany is currently 32 jobs
            # total, nowhere near this limit. Add offset-based pagination if
            # field_keyword_05_count for Germany ever exceeds this.
            "size": 100,
            "from": 0,
            "sort": [{"_score": "desc"}, {"pageviews": "desc"}],
            "lang": "zz",
            "localeSelector": {},
            "sm": {"query": "", "lang": "zz"},
            "_source": ["_id", "title", "url", "field_keyword_08", "field_keyword_18", "field_keyword_19"],
        }}

    def parse(self, raw: Any) -> list[JobPosting]:
        postings = []
        for hit in raw.get("hits", {}).get("hits", []):
            src = hit.get("_source", {})
            postings.append(JobPosting(
                company=self.company,
                external_id=hit.get("_id") or src.get("url", ""),
                title=src.get("title", ""),
                # IBM spells it "Muenchen, DE" (ASCII transliteration), not
                # "München" - see location_aliases.py for the "ibm" entry
                # this requires, same lesson as Ottobrunn/Garching before it
                location=src.get("field_keyword_19"),
                url=src.get("url"),
                department=src.get("field_keyword_08"),
                posted_at=None,
            ))
        return postings


SCRAPER = IbmScraper()
