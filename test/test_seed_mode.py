"""ponytail check: run with `python3 -m test.test_seed_mode` from the repo root."""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("TELEGRAM_CHAT_ID", "123")

from db.models import ScraperHealth
from db.session import SessionLocal, init_db
from scrapers.base import JobPosting
import scheduler_entrypoint as se


def _fake_scraper():
    scraper = MagicMock()
    scraper.company = "acme"
    scraper.run.return_value = [
        JobPosting(company="acme", external_id="1", title="Engineer", location="Munich", url="u"),
    ]
    return scraper


def demo() -> None:
    init_db()
    session = SessionLocal()

    with patch.object(se, "notify_new_job") as mock_notify:
        se.run_scraper(session, _fake_scraper(), seed_mode=True)
        assert mock_notify.call_count == 0, "seed mode must not notify on insert"

    session.query(ScraperHealth).delete()
    session.commit()

    with patch.object(se, "notify_new_job") as mock_notify:
        se.run_scraper(session, _fake_scraper(), seed_mode=False)
        assert mock_notify.call_count == 0, "row already exists from seed run, dedup should block the insert"

    health = session.get(ScraperHealth, "acme")
    assert health.last_success_at is not None, "health tracking must still update in seed mode"

    session.close()
    print("ok")


if __name__ == "__main__":
    demo()
