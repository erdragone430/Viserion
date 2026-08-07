<p align="center">
  <img src="assets/job_dragon.png" alt="JobDragon logo" width="220">
</p>

<h1 align="center">Viserion, the job scraper</h1>

Scrapes company career pages on a schedule, dedups against SQLite, and
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

cp .env.example .env   # fill in DATABASE_URL/SQLITE_DATA_DIR, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

## Bring your own selectors

This project follows a **"Bring Your Own Selectors"** approach. The scraper
code contains the parsing logic and framework, but **all company-specific
targets** (API endpoints, CSS selectors, JSON field mappings, location
parameters, facet IDs) live in external config files under `targets/` that
are **not committed** to the repository.

To make the scrapers work you need to provide your own targets:

```bash
# Copy the example templates for all companies
for f in targets/*.example.json; do
  cp "$f" "targets/$(basename "$f" .example.json).json"
done

# Then fill in the actual values for each company you want to scrape:
#   vim targets/amazon.json
#   vim targets/apple.json
#   ...
```

Each `targets/<company>.json` file contains the endpoint URL, request
parameters, response field names, and (for HTML scrapers) CSS selectors
that the scraper needs. The example files (`targets/*.example.json`)
document the required schema with placeholder values — fill them with
real data from the company's career site.

See [`PLAN.md`](PLAN.md) for a detailed breakdown of what was
externalised and why.

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

## CI / CD

Two GitHub Actions workflows:

| Workflow | Trigger | What it does |
|---|---|---|
| **Test** (`.github/workflows/test.yml`) | Push to `main` | Runs the test suite — `test_clear_chat` and `test_seed_mode` (both in-memory SQLite, no external service needed) |
| **Deploy** (`.github/workflows/deploy.yml`) | Manual (`workflow_dispatch`) | SSHes into the production server, pulls the latest code, and runs `deploy/deploy.sh` to rebuild the dashboard container |

Testing is automatic on every push. Deployment is manual — use the
GitHub Actions UI to trigger a deploy when you want to ship changes.
