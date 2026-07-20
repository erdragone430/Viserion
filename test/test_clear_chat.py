"""ponytail check: run with `python -m test.test_clear_chat` from the repo root."""
from __future__ import annotations

import os
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("TELEGRAM_CHAT_ID", "123")

from db.models import SentTelegramMessage
from db.session import SessionLocal, init_db
from notifier import clear_chat


class FakeResp:
    def __init__(self, status_code):
        self.status_code = status_code
        self.ok = status_code < 300
        self.text = "boom"


def demo() -> None:
    init_db()
    session = SessionLocal()
    session.add_all([
        SentTelegramMessage(chat_id="123", message_id=1),   # will succeed (200)
        SentTelegramMessage(chat_id="123", message_id=2),   # too old (400)
        SentTelegramMessage(chat_id="123", message_id=3),   # transient failure (500) - kept
    ])
    session.commit()

    responses = iter([FakeResp(200), FakeResp(400), FakeResp(500)])
    with patch("notifier.clear_chat.requests.post", side_effect=lambda *a, **k: next(responses)):
        clear_chat.main()

    remaining = [r.message_id for r in session.query(SentTelegramMessage).all()]
    assert remaining == [3], f"expected only message 3 (transient failure) to survive, got {remaining}"
    session.close()
    print("ok:", remaining)


if __name__ == "__main__":
    demo()
