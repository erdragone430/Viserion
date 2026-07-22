from targets.loader import load_target

from ..direct_json import WorkdayScraper

_cfg = load_target("airbus_ds")

if _cfg is not None:
    SCRAPER = WorkdayScraper(
        company="airbus_ds",
        host=_cfg["host"],
        tenant=_cfg["tenant"],
        site=_cfg["site"],
        applied_facets=_cfg.get("applied_facets"),
    )
else:
    SCRAPER = None
