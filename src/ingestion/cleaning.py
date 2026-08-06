from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord

logger = logging.getLogger(__name__)

# Minimum content needed for a record to be embeddable/useful downstream.
MIN_SUMMARY_CHARS = 20
MIN_TITLE_CHARS = 3


def _normalize_field(value: str) -> str:
    """Collapse whitespace and strip. PaperRecord fields are always str, never None."""
    if not value:
        return ""
    return " ".join(value.split())


def _parse_partial_date(value: str) -> pd.Timestamp | None:
    """Parse 'YYYY', 'YYYY-MM', or 'YYYY-MM-DD' into a Timestamp.

    Missing month/day default to 1 (matches Crossref's own convention for
    partial dates). Returns None (pd.NaT-compatible) if unparseable.
    """
    if not value:
        return None
    parts = value.split("-")
    try:
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 1
        day = int(parts[2]) if len(parts) > 2 else 1
        return pd.Timestamp(datetime(year, month, day))
    except (ValueError, IndexError):
        logger.warning("Could not parse date string: %r", value)
        return None


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw PaperRecord list into a DataFrame ready for embedding.

    Pipeline:
    1. Normalize title/summary/authors/categories text.
    2. Parse published/updated into real datetimes.
    3. Compute age_days relative to run_date.
    4. Add helper columns: authors_joined, categories_joined, summary_chars,
       text_for_embedding.
    5. Drop duplicate paper_ids and rows that are too thin to be useful.
    6. Sort by published date (newest first) and return.
    """
    if not records:
        logger.warning("build_clean_dataframe received an empty records list")
        return pd.DataFrame(
            columns=[
                "paper_id", "title", "summary", "authors", "categories",
                "primary_category", "published", "updated", "abs_url",
                "pdf_url", "comment", "published_dt", "updated_dt", "age_days",
                "authors_joined", "categories_joined", "summary_chars",
                "text_for_embedding",
            ]
        )

    df = pd.DataFrame([r.__dict__ for r in records])

    # 1. Normalize text fields
    df["title"] = df["title"].map(_normalize_field)
    df["summary"] = df["summary"].map(_normalize_field)
    df["authors"] = df["authors"].map(lambda names: [_normalize_field(n) for n in names if _normalize_field(n)])
    df["categories"] = df["categories"].map(lambda cats: [_normalize_field(c) for c in cats if _normalize_field(c)])

    # 2. Parse dates
    df["published_dt"] = df["published"].map(_parse_partial_date)
    df["updated_dt"] = df["updated"].map(_parse_partial_date)
    # Fall back to published_dt where updated_dt is missing
    df["updated_dt"] = df["updated_dt"].fillna(df["published_dt"])

    # 3. age_days relative to run_date (NaT-safe)
    run_ts = pd.Timestamp(run_date)
    # Crossref publication dates are date-only and therefore timezone-naive.
    # Normalize an aware run timestamp to UTC-naive before subtraction so
    # pandas does not mix tz-aware and tz-naive datetime values.
    if run_ts.tz is not None:
        run_ts = run_ts.tz_convert("UTC").tz_localize(None)
    df["age_days"] = (run_ts - df["published_dt"]).dt.days

    # 4. Helper columns
    df["authors_joined"] = df["authors"].map(lambda names: ", ".join(names))
    df["categories_joined"] = df["categories"].map(lambda cats: ", ".join(cats))
    df["summary_chars"] = df["summary"].map(len)
    df["text_for_embedding"] = df.apply(
        lambda row: f"{row['title']}\n\n{row['summary']}".strip(),
        axis=1,
    )

    # 5. Drop duplicates and filter thin/invalid rows
    before = len(df)
    df = df.drop_duplicates(subset="paper_id", keep="first")
    df = df[
        (df["title"].str.len() >= MIN_TITLE_CHARS)
        & (df["summary"].str.len() >= MIN_SUMMARY_CHARS)
        & df["published_dt"].notna()
    ]
    dropped = before - len(df)
    if dropped:
        logger.info("Dropped %d invalid/duplicate rows during cleaning", dropped)

    # 6. Sort newest first, reset index
    df = df.sort_values("published_dt", ascending=False).reset_index(drop=True)

    return df
