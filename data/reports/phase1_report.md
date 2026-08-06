# Phase 1 Baseline Report

## Source
- **source_api**: Crossref REST API
- **source_query**: agentic retrieval augmented generation large language model
- **raw_record_count**: 24
- **clean_record_count**: 24

## Retrieval / Evaluation Metrics
- **samples**: 20
- **retrieval_hit_rate**: 1.0
- **mean_token_f1**: 0.75
- **judge_accuracy**: 0.75
- **mean_judge_score**: 4
- **ragas**:
  - context_precision: 0.249999999975
  - context_recall: 0.3333333333333333
  - faithfulness: 0.3333333333333333

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
