from targets.loader import load_target

from ..direct_json import GreenhouseScraper

_cfg = load_target("mongodb")

if _cfg is not None:
    SCRAPER = GreenhouseScraper(
        company="mongodb",
        board_token=_cfg["board_token"],
    )
else:
    SCRAPER = None
