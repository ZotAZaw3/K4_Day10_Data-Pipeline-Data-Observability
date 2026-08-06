from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json

MIN_SUMMARY_CHARS = 40


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Chay data quality checks tren cleaned dataframe va ghi report vao data/quality/."""
    row_count = len(df)
    paper_id_nulls = int(df["paper_id"].isna().sum())
    duplicate_paper_ids = int(df["paper_id"].duplicated().sum())
    title_nulls = int(df["title"].isna().sum())
    summary_too_short = int((df["summary"].fillna("").str.len() < MIN_SUMMARY_CHARS).sum())
    stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum()) if "age_days" in df else 0

    passed = row_count > 0 and paper_id_nulls == 0 and duplicate_paper_ids == 0 and title_nulls == 0

    report = {
        "report_name": report_name,
        "row_count": row_count,
        "paper_id_nulls": paper_id_nulls,
        "duplicate_paper_ids": duplicate_paper_ids,
        "title_nulls": title_nulls,
        "summary_too_short": summary_too_short,
        "stale_rows": stale_rows,
        "passed": passed,
    }
    write_json(settings.paths.quality_dir / f"{report_name}.json", report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Tong hop freshness report tu published/age_days va ghi JSON."""
    published = pd.to_datetime(df["published"], errors="coerce")
    has_dates = published.notna().any()
    stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum()) if "age_days" in df else 0

    report = {
        "latest_published": published.max().date().isoformat() if has_dates else None,
        "oldest_published": published.min().date().isoformat() if has_dates else None,
        "stale_rows": stale_rows,
        "total_rows": len(df),
        "is_fresh": stale_rows == 0,
    }
    write_json(report_path, report)
    return report


def _demo() -> None:
    import tempfile
    from pathlib import Path
    from types import SimpleNamespace

    df = pd.DataFrame(
        [
            {"paper_id": "a1", "title": "Paper One", "summary": "x" * 50, "published": "2024-01-01", "age_days": 10},
            {"paper_id": "a1", "title": "Paper One Dup", "summary": "short", "published": "2020-01-01", "age_days": 900},
        ]
    )
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        settings = SimpleNamespace(
            freshness_threshold_days=180,
            paths=SimpleNamespace(quality_dir=tmp_path / "quality"),
        )

        quality = run_data_quality_checks(df, settings, "demo_quality")
        assert quality["row_count"] == 2
        assert quality["duplicate_paper_ids"] == 1
        assert quality["summary_too_short"] == 1
        assert quality["stale_rows"] == 1
        assert quality["passed"] is False
        assert (tmp_path / "quality" / "demo_quality.json").exists()

        freshness = build_freshness_report(df, settings, tmp_path / "freshness.json")
        assert freshness["latest_published"] == "2024-01-01"
        assert freshness["oldest_published"] == "2020-01-01"
        assert freshness["total_rows"] == 2
        assert freshness["is_fresh"] is False
        assert (tmp_path / "freshness.json").exists()
    print("quality self-check OK")


if __name__ == "__main__":
    _demo()
