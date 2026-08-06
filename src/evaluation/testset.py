from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json

MIN_DOCUMENTS = 1
SAMPLE_SIZE = 5


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Tao evaluation set tu cleaned dataframe.

    Cau hoi duoc viet dung format ma retrieval.qa._extract_answer nhan dien
    (title trong dau nhay don de kich hoat exact lookup + dung extractor),
    nen ground_truth o day phai khop chinh xac metadata cua paper do.
    """
    if len(df) < MIN_DOCUMENTS:
        raise ValueError(f"Need at least {MIN_DOCUMENTS} document(s) to build a test set, got {len(df)}.")

    sample = df.head(min(SAMPLE_SIZE, len(df)))

    templates = [
        ("summary", "What is the paper '{title}' about?", lambda row: first_sentence(row["summary"])),
        ("authors", "Who authored the paper '{title}'?", lambda row: row["authors_joined"]),
        ("date", "When was the paper '{title}' published?", lambda row: row["published"]),
        ("categories", "What categories does the paper '{title}' belong to?", lambda row: row["categories_joined"]),
    ]

    test_set: list[dict[str, Any]] = []
    for _, row in sample.iterrows():
        for question_type, template, ground_truth_fn in templates:
            test_set.append(
                {
                    "id": f"{row['paper_id']}::{question_type}",
                    "question_type": question_type,
                    "question": template.format(title=row["title"]),
                    "ground_truth": ground_truth_fn(row),
                    "ground_truth_doc_ids": [row["paper_id"]],
                }
            )

    write_json(output_path, test_set)
    return test_set


def _demo() -> None:
    import tempfile
    from pathlib import Path

    df = pd.DataFrame(
        [
            {
                "paper_id": "arxiv:1234.5678",
                "title": "Attention Is All You Need",
                "summary": "We propose a new architecture. It relies on attention.",
                "authors_joined": "Vaswani, Shazeer",
                "categories_joined": "cs.CL, cs.LG",
                "published": "2017-06-12",
            }
        ]
    )
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test_set.json"
        rows = build_test_set(df, out)
        assert out.exists()
        assert len(rows) == 4
        by_type = {row["question_type"]: row for row in rows}
        assert "who authored" in by_type["authors"]["question"].lower()
        assert by_type["authors"]["ground_truth"] == "Vaswani, Shazeer"
        assert "when was" in by_type["date"]["question"].lower()
        assert by_type["date"]["ground_truth"] == "2017-06-12"
        assert "what categories" in by_type["categories"]["question"].lower()
        assert by_type["summary"]["ground_truth"] == "We propose a new architecture."
        assert all(row["ground_truth_doc_ids"] == ["arxiv:1234.5678"] for row in rows)
    print("testset self-check OK")


if __name__ == "__main__":
    _demo()
