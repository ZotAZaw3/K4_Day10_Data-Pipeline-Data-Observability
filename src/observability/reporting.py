from __future__ import annotations

from typing import Any

from core.utils import write_text


def _bullets(data: dict[str, Any]) -> str:
    lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"- **{key}**:")
            lines.extend(f"  - {sub_key}: {sub_value}" for sub_key, sub_value in value.items())
        else:
            lines.append(f"- **{key}**: {value}")
    return "\n".join(lines)


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Viet markdown report cho baseline phase tu cac artifact that."""
    sections = [
        "# Phase 1 Baseline Report",
        "",
        "## Source",
        _bullets(source_summary),
        "",
        "## Retrieval / Evaluation Metrics",
        _bullets(metrics),
        "",
        "## Data Quality",
        _bullets(quality),
        "",
        "## Freshness",
        _bullets(freshness),
        "",
    ]
    write_text(report_path, "\n".join(sections))


def _metric_table(baseline: dict[str, Any], corrupted: dict[str, Any], repaired: dict[str, Any]) -> str:
    numeric_keys = [key for key, value in baseline.items() if isinstance(value, (int, float)) and not isinstance(value, bool)]
    lines = [
        "| Metric | Baseline | Corrupted | Repaired | Delta (repaired - baseline) |",
        "| --- | --- | --- | --- | --- |",
    ]
    for key in numeric_keys:
        base_value = baseline.get(key)
        corrupted_value = corrupted.get(key)
        repaired_value = repaired.get(key)
        delta = repaired_value - base_value if isinstance(repaired_value, (int, float)) else "n/a"
        lines.append(f"| {key} | {base_value} | {corrupted_value} | {repaired_value} | {delta} |")
    return "\n".join(lines)


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Viet markdown report so sanh baseline/corrupted/repaired."""
    sections = [
        "# Corruption Impact Report",
        "",
        "## Metrics Comparison",
        _metric_table(baseline_metrics, corrupted_metrics, repaired_metrics),
        "",
        "## Corrupted Data Quality",
        _bullets(corrupted_quality),
        "",
        "## Repaired Data Quality",
        _bullets(repaired_quality),
        "",
        "## Corrupted Freshness",
        _bullets(corrupted_freshness),
        "",
        "## Repaired Freshness",
        _bullets(repaired_freshness),
        "",
    ]
    write_text(report_path, "\n".join(sections))


def _demo() -> None:
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        phase1_path = tmp_path / "phase1_report.md"
        generate_phase1_report(
            phase1_path,
            source_summary={"source_api": "Crossref REST API", "raw_records": 24},
            metrics={"samples": 20, "retrieval_hit_rate": 0.9, "ragas": {"skipped": "..."}},
            quality={"row_count": 20, "passed": True},
            freshness={"stale_rows": 0, "is_fresh": True},
        )
        text = phase1_path.read_text(encoding="utf-8")
        assert "# Phase 1 Baseline Report" in text
        assert "retrieval_hit_rate" in text
        assert "skipped" in text  # nested dict flattened

        comparison_path = tmp_path / "corruption_report.md"
        generate_corruption_report(
            comparison_path,
            baseline_metrics={"retrieval_hit_rate": 0.9},
            corrupted_metrics={"retrieval_hit_rate": 0.4},
            repaired_metrics={"retrieval_hit_rate": 0.85},
            corrupted_quality={"passed": False},
            repaired_quality={"passed": True},
            corrupted_freshness={"is_fresh": False},
            repaired_freshness={"is_fresh": True},
        )
        table_text = comparison_path.read_text(encoding="utf-8")
        assert "| retrieval_hit_rate | 0.9 | 0.4 | 0.85" in table_text
    print("reporting self-check OK")


if __name__ == "__main__":
    _demo()
