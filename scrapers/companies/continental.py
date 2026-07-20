from __future__ import annotations

import json
from typing import Any

import requests

from ..base import JobPosting
from ..direct_json import DirectJsonScraper

# Continental's own coordinates don't move; same reasoning as Amazon's static
# Munich lat/long (see amazon.py) - a live geocode for one static city is more
# moving parts than the constant it would produce.
MUNICH_LAT = 48.1391
MUNICH_LON = 11.5802


class ContinentalScraper(DirectJsonScraper):
    company = "continental"
    url = "https://jobs.continental.com/en/api/result-list/pagetype-jobs/"
    method = "POST"

    def request_kwargs(self) -> dict:
        location = json.dumps({
            "title": "Munich, Germany",
            "type": "location",
            "coordinates": {"latitude": MUNICH_LAT, "longitude": MUNICH_LON},
        })
        return {
            # Confirmed live: a WAF 403s a bare requests.post() with no
            # Referer/User-Agent, but doesn't need any cookies/session.
            "headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                "Referer": "https://jobs.continental.com/en/",
                "Origin": "https://jobs.continental.com",
            },
            "data": {
                "tx_conjobs_api[filter][location]": location,
                # radius left at the site's own default (50km) rather than widening -
                # 100km was confirmed to pull in cross-border Austrian retail/tire-shop
                # jobs that aren't really "Munich", so the default is the more precise
                # choice even though it means 0 results as of this writing.
                "tx_conjobs_api[itemsPerPage]": 100,
            },
        }

    def parse(self, raw: Any) -> list[JobPosting]:
        postings = []
        for job in raw.get("result", {}).get("list", []):
            postings.append(JobPosting(
                company=self.company,
                external_id=job.get("refNumber") or job.get("internalId"),
                title=job.get("title", ""),
                location=", ".join(filter(None, [job.get("cityLabel"), job.get("countryLabel")])) or None,
                url=job.get("absoluteUrl"),
                department=job.get("fieldOfWorkLabel") or None,
                posted_at=None,
            ))
        return postings


SCRAPER = ContinentalScraper()
