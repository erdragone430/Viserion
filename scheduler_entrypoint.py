from dotenv import load_dotenv

load_dotenv()  # must run before db.session reads DATABASE_URL at import time

import argparse
import logging
import os
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert as pg_insert

from db.models import JobPostingRow, ScraperHealth
from db.session import SessionLocal, init_db
from notifier.telegram import notify_new_job, notify_scraper_health
from scrapers.companies import (
    airbus_ds,
    amazon,
    apple,
    celonis,
    continental,
    flixbus,
    google,
    ibm,
    infineon,
    isar_aerospace,
    man,
    meta,
    microsoft,
    personio,
    rohde_schwarz,
    sap,
    siemens,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCRAPERS = [
    amazon.SCRAPER,
    microsoft.SCRAPER,
    infineon.SCRAPER,
    man.SCRAPER,
    isar_aerospace.SCRAPER,
    celonis.SCRAPER,
    personio.SCRAPER,
    siemens.SCRAPER,
    rohde_schwarz.SCRAPER,
    flixbus.SCRAPER,
    sap.SCRAPER,
    google.SCRAPER,
    apple.SCRAPER,
    meta.SCRAPER,
    airbus_ds.SCRAPER,
    continental.SCRAPER,
    ibm.SCRAPER,
]

FAILURE_ALERT_THRESHOLD = 3


def run_scraper(session, scraper, seed_mode: bool = False) -> None:
    health = session.get(ScraperHealth, scraper.company)
    if health is None:
        health = ScraperHealth(company=scraper.company, consecutive_failures=0)
        session.add(health)

    health.last_run_at = datetime.now(timezone.utc)

    try:
        postings = scraper.run()
    except Exception as exc:
        health.consecutive_failures += 1
        health.last_error = str(exc)
        logger.exception("scraper failed: %s", scraper.company)
        if health.consecutive_failures >= FAILURE_ALERT_THRESHOLD:
            notify_scraper_health(scraper.company, health.consecutive_failures, str(exc))
        session.commit()
        return

    health.last_success_at = datetime.now(timezone.utc)
    health.consecutive_failures = 0
    health.last_error = None

    for posting in postings:
        stmt = pg_insert(JobPostingRow).values(
            company=posting.company,
            external_id=posting.external_id,
            title=posting.title,
            location=posting.location,
            url=posting.url,
            department=posting.department,
            posted_at=posting.posted_at,
        ).on_conflict_do_nothing(index_elements=["company", "external_id"])
        result = session.execute(stmt)
        if result.rowcount and not seed_mode:
            notify_new_job(posting)

    session.commit()
    logger.info("%s: %d matching postings", scraper.company, len(postings))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="store_true", help="suppress new-job notifications (for seeding a fresh DB)")
    args = parser.parse_args()

    seed_mode = args.seed or os.environ.get("SEED_MODE", "false").lower() == "true"
    if seed_mode:
        logger.info("Running in SEED MODE — notifications for new jobs are suppressed this run")

    init_db()
    session = SessionLocal()
    try:
        for scraper in SCRAPERS:
            try:
                run_scraper(session, scraper, seed_mode=seed_mode)
            except Exception:
                session.rollback()
                logger.exception("unhandled error running %s, skipping", scraper.company)
    finally:
        session.close()


if __name__ == "__main__":
    main()
