from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root, for db.session below

load_dotenv()

from db.session import engine  # reuse the scraper's existing engine/config, no duplicate connection logic

FAVICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "job_dragon.png"

st.set_page_config(
    page_title="Job Postings",
    page_icon=str(FAVICON_PATH),
    layout="wide")


@st.cache_data(ttl=300)
def load_postings() -> pd.DataFrame:
    df = pd.read_sql(
        "SELECT company, external_id, title, location, url, department, posted_at, first_seen_at "
        "FROM job_postings",
        engine,
    )
    df["effective_date"] = df["posted_at"].fillna(df["first_seen_at"])
    return df


df = load_postings()

st.title("Job Postings Dashboard")

if df.empty:
    st.info("No postings in the database yet.")
    st.stop()

companies = sorted(df["company"].dropna().unique().tolist())
min_date = df["effective_date"].min().date()
max_date = df["effective_date"].max().date()
default_start = max(min_date, date.today() - timedelta(days=30))

filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 2])
with filter_col1:
    # empty selection = no company filter applied, so the dropdown doesn't
    # default to a wall of pills for every company
    selected_companies = st.multiselect("Company", companies, placeholder="All companies")
with filter_col2:
    date_range = st.date_input("Date range", value=(default_start, max_date), min_value=min_date, max_value=max_date)
with filter_col3:
    keyword = st.text_input("Keyword search (title / department)")

filtered = df if not selected_companies else df[df["company"].isin(selected_companies)]

if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
    filtered = filtered[(filtered["effective_date"].dt.date >= start) & (filtered["effective_date"].dt.date <= end)]

if keyword:
    kw = keyword.lower()
    filtered = filtered[
        filtered["title"].str.lower().str.contains(kw, na=False)
        | filtered["department"].str.lower().str.contains(kw, na=False)
    ]

filtered = filtered.sort_values("first_seen_at", ascending=False).reset_index(drop=True)

col1, col2 = st.columns(2)
col1.metric("Postings shown", len(filtered))
col2.metric("Distinct companies", filtered["company"].nunique())

display_cols = ["company", "title", "location", "department", "posted_at", "first_seen_at"]
event = st.dataframe(
    filtered[display_cols],
    width="stretch",
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
)

selected_rows = event.selection.rows if event and event.selection else []
if selected_rows:
    row = filtered.iloc[selected_rows[0]]

    def fmt(val):
        return "—" if pd.isna(val) else val

    st.subheader(row["title"])
    st.write(f"**Company:** {row['company']}")
    st.write(f"**Location:** {fmt(row['location'])}")
    st.write(f"**Department:** {fmt(row['department'])}")
    st.write(f"**Posted at:** {fmt(row['posted_at'])}")
    st.write(f"**First seen:** {fmt(row['first_seen_at'])}")
    if pd.notna(row["url"]):
        st.link_button("Open original posting ↗", row["url"])
else:
    st.caption("Click a row above to see full details.")
