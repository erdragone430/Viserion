# vyserion_job_scraper

## Resetting the database

After recreating the DB (e.g. `docker-compose down -v && docker-compose up -d`,
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
