# Phase 1 Baseline Report

## Source
- **source_api**: Crossref REST API
- **source_query**: agentic retrieval augmented generation large language model
- **raw_record_count**: 24
- **clean_record_count**: 24

## Retrieval / Evaluation Metrics
- **samples**: 20
- **retrieval_hit_rate**: 1.0
- **mean_token_f1**: 1.0
- **judge_accuracy**: 1.0
- **mean_judge_score**: 5
- **ragas**:
  - context_precision: 0.49999999995
  - context_recall: 0.5
  - faithfulness: 0.4875

## Data Quality
- **report_name**: baseline_quality
- **row_count**: 24
- **paper_id_nulls**: 0
- **duplicate_paper_ids**: 0
- **title_nulls**: 0
- **summary_too_short**: 0
- **stale_rows**: 0
- **passed**: True

## Freshness
- **latest_published**: 2026-08-01
- **oldest_published**: 2026-02-12
- **stale_rows**: 0
- **total_rows**: 24
- **is_fresh**: True
