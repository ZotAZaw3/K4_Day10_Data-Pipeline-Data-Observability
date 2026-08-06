# Corruption Impact Report

## Metrics Comparison
| Metric | Baseline | Corrupted | Repaired | Delta (repaired - baseline) |
| --- | --- | --- | --- | --- |
| samples | 20 | 20 | 20 | 0 |
| retrieval_hit_rate | 1.0 | 0.4 | 1.0 | 0.0 |
| mean_token_f1 | 0.75 | 0.2537037037037037 | 0.75 | 0.0 |
| judge_accuracy | 0.75 | 0.25 | 0.75 | 0.0 |
| mean_judge_score | 4 | 2.3 | 4 | 0 |

## Corrupted Data Quality
- **report_name**: corrupted_quality
- **row_count**: 23
- **paper_id_nulls**: 0
- **duplicate_paper_ids**: 2
- **title_nulls**: 0
- **summary_too_short**: 4
- **stale_rows**: 3
- **passed**: False

## Repaired Data Quality
- **report_name**: repaired_quality
- **row_count**: 24
- **paper_id_nulls**: 0
- **duplicate_paper_ids**: 0
- **title_nulls**: 0
- **summary_too_short**: 0
- **stale_rows**: 0
- **passed**: True

## Corrupted Freshness
- **latest_published**: 2026-07-03
- **oldest_published**: 2010-01-01
- **stale_rows**: 3
- **total_rows**: 23
- **is_fresh**: False

## Repaired Freshness
- **latest_published**: 2026-08-01
- **oldest_published**: 2026-02-12
- **stale_rows**: 0
- **total_rows**: 24
- **is_fresh**: True
