from __future__ import annotations

import logging

from core.config import load_settings
from core.utils import now_utc, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.agent import build_agent, run_agent_question
from retrieval.index import LocalEmbeddingIndex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    settings = load_settings()

    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        records = fetch_source_records(settings)
    else:
        records = load_raw_records(settings.paths.raw_records_json)

    clean_df = build_clean_dataframe(records, run_date=now_utc())
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))

    index = LocalEmbeddingIndex.build(
        clean_df, settings, embeddings_output_path=settings.paths.embeddings_json
    )

    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        build_test_set(clean_df, settings.paths.eval_testset)

    bundle = evaluate_pipeline(
        settings,
        index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    quality = run_data_quality_checks(clean_df, settings, "baseline_quality")
    freshness = build_freshness_report(clean_df, settings, settings.paths.freshness_report)

    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary={
            "source_api": settings.source_api,
            "source_query": settings.source_query,
            "raw_record_count": len(records),
            "clean_record_count": len(clean_df),
        },
        metrics=bundle.summary,
        quality=quality,
        freshness=freshness,
    )

    demo_answers: list[dict[str, str]] = []
    if len(clean_df) > 0:
        try:
            agent = build_agent(settings, index)
            sample_title = clean_df.iloc[0]["title"]
            for question in (
                f"What is the paper '{sample_title}' about?",
                "What papers are indexed in this corpus?",
            ):
                demo_answers.append({"question": question, "answer": run_agent_question(agent, question)})
        except Exception as exc:  # pragma: no cover - demo is best-effort
            logger.warning("Agent demo skipped: %s", exc)
    write_json(settings.paths.demo_answers, demo_answers)

    logger.info("Phase 1 pipeline complete. Report at %s", settings.paths.baseline_report)


if __name__ == "__main__":
    main()
