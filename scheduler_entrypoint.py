from dotenv import load_dotenv

load_dotenv()  # must run before db.session reads DATABASE_URL at import time

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timezone

import sqlalchemy.exc
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

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
    #ibm,
    infineon,
    isar_aerospace,
    man,
    #meta,
    microsoft,
    mongodb,
    personio,
    rohde_schwarz,
    sap,
    scalable_capital,
    siemens,
    uncountable,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCRAPERS = [s for s in [
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
    #meta.SCRAPER,
    airbus_ds.SCRAPER,
    continental.SCRAPER,
    #ibm.SCRAPER,
    mongodb.SCRAPER,  # temp: internship season (~end Sept 2026), comment out after
    uncountable.SCRAPER,
    scalable_capital.SCRAPER,
] if s is not None]

FAILURE_ALERT_THRESHOLD = 3


def run_scraper(session, scraper, seed_mode: bool = False) -> None:
    try:
        health = session.get(ScraperHealth, scraper.company)
        if health is None:
            health = ScraperHealth(company=scraper.company, consecutive_failures=0)
            session.add(health)

        health.last_run_at = datetime.now(timezone.utc)

        try:
            postings = scraper.run()
        except sqlalchemy.exc.OperationalError:
            raise
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
            stmt = sqlite_insert(JobPostingRow).values(
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
    except sqlalchemy.exc.OperationalError:
        logger.exception("DB error in %s, aborting scraper run", scraper.company)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="store_true", help="suppress new-job notifications (for seeding a fresh DB)")
    args = parser.parse_args()

    seed_mode = args.seed or os.environ.get("SEED_MODE", "false").lower() == "true"
    if seed_mode:
        logger.info("Running in SEED MODE — notifications for new jobs are suppressed this run")

    last_err = None
    for attempt in range(3):
        try:
            init_db()
            last_err = None
            break
        except sqlalchemy.exc.OperationalError as e:
            last_err = e
            logger.warning("DB not ready (attempt %d/3), retrying…", attempt + 1)
            time.sleep(2 ** attempt)
    if last_err is not None:
        logger.critical("DB unreachable after 3 attempts, exiting")
        notify_scraper_health("SYSTEM", 0, f"DB unreachable after 3 attempts: {last_err}")
        sys.exit(1)

    session = SessionLocal()
    try:
        for scraper in SCRAPERS:
            try:
                run_scraper(session, scraper, seed_mode=seed_mode)
            except sqlalchemy.exc.OperationalError:
                logger.critical("DB connection lost, aborting run")
                session.rollback()
                sys.exit(1)
            except Exception:
                session.rollback()
                logger.exception("unhandled error running %s, skipping", scraper.company)
    finally:
        session.close()


if __name__ == "__main__":
    main()
