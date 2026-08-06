from __future__ import annotations

from datetime import datetime

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord

MIN_TITLE_CHARS = 3

CLEAN_COLUMNS = [
    "paper_id", "title", "summary", "authors", "categories", "primary_category",
    "published", "updated", "abs_url", "pdf_url", "comment",
    "authors_joined", "categories_joined", "summary_chars", "text_for_embedding", "age_days",
]


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw PaperRecords into an embed-ready dataframe."""
    rows = [
        {
            "paper_id": record.paper_id,
            "title": normalize_whitespace(record.title),
            "summary": normalize_whitespace(record.summary),
            "authors": [normalize_whitespace(a) for a in record.authors if a],
            "categories": [normalize_whitespace(c) for c in record.categories if c],
            "primary_category": normalize_whitespace(record.primary_category),
            "published": record.published,
            "updated": record.updated,
            "abs_url": record.abs_url,
            "pdf_url": record.pdf_url,
            "comment": normalize_whitespace(record.comment),
        }
        for record in records
    ]
    if not rows:
        return pd.DataFrame(columns=CLEAN_COLUMNS)

    df = pd.DataFrame(rows)
    df["authors_joined"] = df["authors"].apply(compact_join)
    df["categories_joined"] = df["categories"].apply(compact_join)
    df["summary_chars"] = df["summary"].str.len()
    df["text_for_embedding"] = (
        df["title"] + ". " + df["summary"] + " Categories: " + df["categories_joined"]
    ).str.strip()

    published_dt = pd.to_datetime(df["published"], errors="coerce")
    run_ts = pd.Timestamp(run_date)
    if run_ts.tzinfo is not None:
        run_ts = run_ts.tz_localize(None)
    df["age_days"] = (run_ts - published_dt).dt.days

    df = df.drop_duplicates(subset="paper_id", keep="first")
    df = df[(df["paper_id"].astype(bool)) & (df["title"].str.len() >= MIN_TITLE_CHARS)]
    df = df.sort_values("published", ascending=False).reset_index(drop=True)
    return df
