from targets.loader import load_target

from ..direct_json import GreenhouseScraper

_cfg = load_target("isar_aerospace")

if _cfg is not None:
    SCRAPER = GreenhouseScraper(
        company="isar_aerospace",
        board_token=_cfg["board_token"],
    )
else:
    SCRAPER = None
