from targets.loader import load_target

from ..direct_json import PcsxScraper

_cfg = load_target("microsoft")

if _cfg is not None:
    SCRAPER = PcsxScraper(
        company="microsoft",
        host=_cfg["host"],
        domain=_cfg["domain"],
        location_query=_cfg.get("location_query", "Munich"),
    )
else:
    SCRAPER = None
