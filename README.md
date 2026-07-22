<p align="center">
  <img src="assets/job_dragon.png" alt="JobDragon logo" width="220">
</p>

<h1 align="center">Viserion, the job scraper</h1>

Scrapes company career pages on a schedule, dedups against Postgres, and
sends a Telegram notification for every genuinely new posting. A Streamlit
dashboard gives a browsable view of everything collected plus per-scraper
health.

## Companies tracked

Amazon, Microsoft, Infineon, MAN, Isar Aerospace, Celonis, Personio, Siemens,
Rohde & Schwarz, FlixBus, SAP, Google, Apple, Meta, Airbus DS, Continental,
IBM — see `scrapers/companies/`.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

cp .env.example .env   # fill in DATABASE_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

## Running

```bash
python3 scheduler_entrypoint.py   # one pass over every scraper in SCRAPERS
```

Run it on a schedule (cron, systemd timer, etc.) for continuous polling.

## Dashboard

```bash
docker compose up -d --build dashboard   # depends on the db service, see below
```

Streamlit UI at `http://localhost:8501`.

## Database

```bash
docker compose up -d db
```

### Resetting the database

After recreating the DB (e.g. `docker compose down -v && docker compose up -d`,
or a password/port change), the first run has no prior rows to dedup against,
so every job scraped looks "new" and would normally flood Telegram with one
notification per posting.

Run once in seed mode first to populate the DB silently, then switch back to
normal runs:

```bash
SEED_MODE=true python3 scheduler_entrypoint.py
# or: python3 scheduler_entrypoint.py --seed

python3 scheduler_entrypoint.py   # normal hourly run from here on
```

Seed mode still fetches, dedups, and inserts postings, and still updates
`scraper_health` normally — it only suppresses the per-job Telegram
notification. Scraper-health failure alerts are never suppressed.

## Deployment

`deploy/deploy.sh` runs on the production server over SSH (see
`.github/workflows/deploy.yml`) after `git pull`, and rebuilds the dashboard
container.
