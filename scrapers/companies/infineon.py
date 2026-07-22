from targets.loader import load_target

from ..direct_json import PcsxScraper

_cfg = load_target("infineon")
SCRAPER = PcsxScraper(
    company="infineon",
    host=_cfg["host"],
    domain=_cfg["domain"],
    location_query=_cfg.get("location_query", "Munich"),
)
