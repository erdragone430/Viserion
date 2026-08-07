"""One-shot data copy: existing Postgres DB -> a new SQLite file.

Usage:
    python3 scripts/migrate_postgres_to_sqlite.py sqlite:////opt/job_scraper/data/jobs.db

Reads SOURCE_DATABASE_URL (or DATABASE_URL) from the environment for Postgres.
"""
import os
import sys

from sqlalchemy import create_engine, select

from db.models import Base

CHUNK_SIZE = 1000


def migrate(source_url: str, target_url: str) -> None:
    src = create_engine(source_url)
    dst = create_engine(target_url)
    Base.metadata.create_all(dst)

    with src.connect() as sconn, dst.begin() as dconn:
        for table in Base.metadata.sorted_tables:
            rows = sconn.execute(select(table)).mappings().all()
            for i in range(0, len(rows), CHUNK_SIZE):
                chunk = rows[i : i + CHUNK_SIZE]
                if chunk:
                    dconn.execute(table.insert(), [dict(r) for r in chunk])
            print(f"{table.name}: copied {len(rows)} rows")

    # ponytail: simplest correctness check for a data-copy script is a
    # post-copy row count diff, not a mocked unit test.
    with src.connect() as sconn, dst.connect() as dconn:
        mismatches = []
        for table in Base.metadata.sorted_tables:
            src_count = len(sconn.execute(select(table)).fetchall())
            dst_count = len(dconn.execute(select(table)).fetchall())
            if src_count != dst_count:
                mismatches.append((table.name, src_count, dst_count))
        if mismatches:
            for name, s, d in mismatches:
                print(f"MISMATCH {name}: source={s} target={d}", file=sys.stderr)
            sys.exit(1)
        print("verified: row counts match for all tables")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: migrate_postgres_to_sqlite.py <sqlite-target-url>")
    source = os.environ.get("SOURCE_DATABASE_URL") or os.environ["DATABASE_URL"]
    migrate(source, sys.argv[1])
