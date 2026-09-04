from targets.loader import load_target

from ..direct_json import AshbyScraper

_cfg = load_target("uncountable")

if _cfg is not None:
    SCRAPER = AshbyScraper(
        company="uncountable",
        org_slug=_cfg["org_slug"],
    )
else:
    SCRAPER = None
