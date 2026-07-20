from sqlalchemy import Column, DateTime, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class JobPostingRow(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True)
    company = Column(Text, nullable=False)
    external_id = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    location = Column(Text)
    url = Column(Text)
    department = Column(Text)
    posted_at = Column(DateTime)
    first_seen_at = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("company", "external_id"),)


class ScraperHealth(Base):
    __tablename__ = "scraper_health"

    company = Column(Text, primary_key=True)
    last_success_at = Column(DateTime)
    last_run_at = Column(DateTime)
    consecutive_failures = Column(Integer, default=0)
    last_error = Column(Text)
