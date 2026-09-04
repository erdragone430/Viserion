from targets.loader import load_target

from ..direct_json import SmartRecruitersScraper

_cfg = load_target("scalable_capital")

if _cfg is not None:
    SCRAPER = SmartRecruitersScraper(
        company="scalable_capital",
        company_identifier=_cfg["company_identifier"],
    )
else:
    SCRAPER = None
