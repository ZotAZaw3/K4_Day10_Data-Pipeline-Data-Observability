from __future__ import annotations

import random

import pandas as pd

from core.utils import write_json

RANDOM_SEED = 42
DROP_LATEST_FRACTION = 0.15
BLANK_SUMMARY_FRACTION = 0.15
NOISE_FRACTION = 0.15
TRUNCATE_TITLE_FRACTION = 0.15
STALE_DATE_FRACTION = 0.15
DUPLICATE_FRACTION = 0.10
STALE_PUBLISHED_DATE = "2010-01-01"
NOISE_SUFFIX = " asldkj q#w#e RANDOM_NOISE_TOKEN_9182"


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate several kinds of real-world data corruption on a clean dataframe."""
    rng = random.Random(RANDOM_SEED)
    corrupted = df.reset_index(drop=True).copy()
    log: dict[str, object] = {"original_row_count": len(corrupted)}

    def sample_indices(fraction: float) -> list[int]:
        if len(corrupted) == 0:
            return []
        n = max(1, int(len(corrupted) * fraction))
        return rng.sample(range(len(corrupted)), min(n, len(corrupted)))

    n_drop = max(1, int(len(corrupted) * DROP_LATEST_FRACTION)) if len(corrupted) > 1 else 0
    log["dropped_latest_paper_ids"] = corrupted.head(n_drop)["paper_id"].tolist()
    corrupted = corrupted.iloc[n_drop:].reset_index(drop=True)

    blanked = sample_indices(BLANK_SUMMARY_FRACTION)
    log["blanked_summary_paper_ids"] = corrupted.loc[blanked, "paper_id"].tolist()
    corrupted.loc[blanked, "summary"] = ""

    noised = sample_indices(NOISE_FRACTION)
    log["noise_injected_paper_ids"] = corrupted.loc[noised, "paper_id"].tolist()
    corrupted.loc[noised, "summary"] = corrupted.loc[noised, "summary"].fillna("") + NOISE_SUFFIX

    truncated = sample_indices(TRUNCATE_TITLE_FRACTION)
    log["truncated_title_paper_ids"] = corrupted.loc[truncated, "paper_id"].tolist()
    corrupted.loc[truncated, "title"] = corrupted.loc[truncated, "title"].str.slice(0, 8)

    staled = sample_indices(STALE_DATE_FRACTION)
    log["stale_date_paper_ids"] = corrupted.loc[staled, "paper_id"].tolist()
    corrupted.loc[staled, "published"] = STALE_PUBLISHED_DATE
    if "age_days" in corrupted.columns:
        stale_age = (pd.Timestamp.now() - pd.Timestamp(STALE_PUBLISHED_DATE)).days
        corrupted.loc[staled, "age_days"] = stale_age

    n_dup = max(1, int(len(corrupted) * DUPLICATE_FRACTION)) if len(corrupted) else 0
    dup_idx = rng.sample(range(len(corrupted)), min(n_dup, len(corrupted))) if len(corrupted) else []
    duplicated_rows = corrupted.iloc[dup_idx]
    log["duplicated_paper_ids"] = duplicated_rows["paper_id"].tolist()
    corrupted = pd.concat([corrupted, duplicated_rows], ignore_index=True)

    corrupted["text_for_embedding"] = (
        corrupted["title"] + ". " + corrupted["summary"].fillna("") + " Categories: " + corrupted["categories_joined"]
    ).str.strip()

    log["final_row_count"] = len(corrupted)
    write_json(output_log_path, log)
    return corrupted
