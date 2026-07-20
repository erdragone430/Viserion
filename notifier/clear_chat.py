"""Manual CLI: delete every message this bot has sent to the chat.

Run with: python -m notifier.clear_chat

Telegram's Bot API has no "clear chat" call - a bot can only delete
messages it sent itself, and only within 48h of sending. Older messages
will fail to delete (400) and are dropped from tracking since there's
nothing more we can do about them.
"""
from __future__ import annotations

import logging

import requests
from dotenv import load_dotenv

load_dotenv()

from db.models import SentTelegramMessage
from db.session import SessionLocal, init_db
from notifier.telegram import BOT_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    init_db()
    session = SessionLocal()
    try:
        rows = session.query(SentTelegramMessage).all()
        deleted = failed = 0
        for row in rows:
            resp = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage",
                json={"chat_id": row.chat_id, "message_id": row.message_id},
                timeout=10,
            )
            if resp.ok or resp.status_code == 400:
                # 400 = already gone / too old (>48h) - nothing more we can do, drop it
                session.delete(row)
                deleted += resp.ok
                failed += resp.status_code == 400
            else:
                logger.warning("deleteMessage failed for %s: %s", row.message_id, resp.text)
        session.commit()
        logger.info("cleared %d messages (%d could not be deleted - too old/already gone)", deleted, failed)
    finally:
        session.close()


if __name__ == "__main__":
    main()
