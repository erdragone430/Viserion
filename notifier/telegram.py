import os

import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def _send(text: str) -> None:
    resp = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
        timeout=10,
    )
    resp.raise_for_status()
    message_id = resp.json()["result"]["message_id"]

    # local import: avoids a DB/session dependency for callers that only send
    from db.models import SentTelegramMessage
    from db.session import SessionLocal
    session = SessionLocal()
    try:
        session.add(SentTelegramMessage(chat_id=str(CHAT_ID), message_id=message_id))
        session.commit()
    finally:
        session.close()


def notify_new_job(posting) -> None:
    lines = [f"🆕 <b>New job — {posting.company}</b>", posting.title]
    if posting.location:
        lines.append(f"📍 {posting.location}")
    if posting.url:
        lines.append(posting.url)
    _send("\n".join(lines))


def notify_scraper_health(company: str, consecutive_failures: int, last_error: str) -> None:
    _send(
        f"⚠️ <b>SCRAPER HEALTH ALERT</b>\n"
        f"{company} has failed {consecutive_failures} times in a row — may be broken.\n"
        f"Last error: {last_error}"
    )
