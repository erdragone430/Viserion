from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from config.location_aliases import matches_location


@dataclass
class JobPosting:
    company: str
    external_id: str
    title: str
    location: Optional[str]
    url: Optional[str]
    department: Optional[str] = None
    posted_at: Optional[datetime] = None


class BaseScraper(ABC):
    company: str  # slug used for DB rows and the location_aliases lookup

    @abstractmethod
    def fetch_raw(self) -> Any:
        """Perform the HTTP call(s) and return the raw response payload."""

    @abstractmethod
    def parse(self, raw: Any) -> list[JobPosting]:
        """Turn the raw payload into JobPosting objects."""

    def filter_location(self, postings: list[JobPosting]) -> list[JobPosting]:
        return [p for p in postings if matches_location(p.location or "", self.company)]

    def run(self) -> list[JobPosting]:
        return self.filter_location(self.parse(self.fetch_raw()))
