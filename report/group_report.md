# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                                                             |
| ------------------ | --------------------------------------------------------------------- |
| Khóa/Lớp         | K4                                                                    |
| Tên nhóm         | FIFO                                                                  |
| Repository         | https://github.com/ZotAZaw3/K4_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06                                                            |

### Thành viên và phân công

| STT | Họ và tên | MSSV   | Vai trò chính | Module/deliverable sở hữu |
| --: | ------------ | ------ | --------------- | --------------------------- |
|   1 | Nguyễn Mai Huy | 2A202601712 | Data, ingestion và corruption owner | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/ingestion/corruption.py`; raw/clean/corrupted/repaired artifacts trong `data/raw/`, `data/clean/` |
|   2 | Bùi Minh Long | 2A202601462 | Evaluation & Observability owner | `src/evaluation/testset.py`, `src/observability/quality.py`, `src/observability/reporting.py`, `src/observability/correlation.py`; `data/eval/test_set.json`, `data/quality/`, `data/reports/` |
|   3 | Nguyễn Quang Huy | 2A202601120 | Pipeline integration, evaluation và debugging owner | `src/evaluation/metrics.py`, `src/core/utils.py`, timezone/JSON/Ragas fixes trong `src/ingestion/cleaning.py`; `data/results/` (baseline/corrupted/repaired metrics) |

## 2. Tóm tắt kết quả

Nhóm đã chạy thành công toàn bộ pipeline end-to-end: fetch 24 record thật từ Crossref, làm sạch thành 24 dòng dữ liệu (`data/clean/`), build index ChromaDB với embedding MiniLM, sinh 20 câu hỏi evaluation (`data/eval/test_set.json`) và đo baseline đạt `retrieval_hit_rate = 1.0`, `mean_token_f1 = 1.0`, `judge_accuracy = 1.0`, `mean_judge_score = 5`, quality/freshness đều pass (24/24 dòng sạch, không stale). Corruption (`RANDOM_SEED = 42`) drop 3 record mới nhất, blank summary 3 record, inject noise 3 record, truncate title 3 record, làm stale date 3 record và duplicate 2 record, khiến dataset còn 23 dòng, quality/freshness fail (2 duplicate, 4 summary quá ngắn, 3 stale row), kéo `retrieval_hit_rate` xuống 0.4 và `mean_judge_score` xuống 2.9. Ảnh hưởng rõ nhất đến retrieval là **drop record mới nhất**: 3/5 paper được lấy mẫu vào test set (12/20 câu hỏi) bị xoá hẳn khỏi index trước khi search, nên đây là nguyên nhân chính của việc retrieval giảm 60 điểm phần trăm, không chỉ do nội dung bị nhiễu. Repair (rebuild lại từ `crossref_records.json` gốc, không phải vá đè lên dữ liệu lỗi) khôi phục hoàn toàn: quality/freshness quay lại pass/fresh (24/24, 0 duplicate, 0 stale), và các metric agent (`retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`, `mean_judge_score`) trở lại đúng mức baseline (1.0/1.0/1.0/5). Blocker quan trọng nhất còn lại không nằm ở baseline mà ở dữ liệu nguồn: Crossref snapshot thiếu hoàn toàn trường `subject` (24/24 record không có category), nên câu hỏi loại `categories` phải được viết lại thành câu hỏi về nội dung/phạm vi paper thay vì đúng category thật; một `timezone mismatch` giữa `now_utc()` (UTC-aware) và `published_dt` (naive) từng chặn việc chạy lại cleaning và đã được vá tại boundary của `cleaning.py`.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response/raw records (data/raw/)
    -> cleaning và data modeling (data/clean/)
    -> embedding (MiniLM) + ChromaDB index
    -> evaluation baseline (data/eval/test_set.json, data/results/baseline_metrics.json)
    -> quality/freshness reports (data/quality/)
    -> corruption (seed 42, data/results/corruption_log.json)
    -> re-index và re-evaluate corrupted (data/results/corrupted_metrics.json)
    -> repair từ raw records gốc (data/clean/papers_clean_repaired.*)
    -> comparison report (data/reports/corruption_report.md)
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref `/works` API (query + filter) | Fetch với retry/backoff (429/500/502/503/504), parse thành `PaperRecord` | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Nguyễn Mai Huy |
| Cleaning          | Raw records | Chuẩn hoá whitespace, parse date, tính `age_days`, tạo `text_for_embedding`, loại null/duplicate/quá ngắn, fix timezone khi trừ `now_utc()` | `data/clean/papers_clean.csv/.json` (24 dòng) | Nguyễn Mai Huy (rule cleaning) + Nguyễn Quang Huy (fix timezone) |
| Embedding/index   | Cleaned dataframe | Embed `text_for_embedding` bằng `sentence-transformers/all-MiniLM-L6-v2`, nạp ChromaDB, giữ `paper_id` trong metadata | Chroma collection (baseline/corrupted/repaired) | Cả nhóm (dùng chung `src/retrieval/index.py`) |
| Evaluation        | Cleaned dataframe | Sinh 20 câu hỏi (4 loại × 5 paper) với `ground_truth`/`ground_truth_doc_ids` khớp logic `_extract_answer`; tính `retrieval_hit_rate`, `token_f1`, `judge_accuracy`, Ragas | `data/eval/test_set.json`, `data/results/*_metrics.json` | Bùi Minh Long (testset) + Nguyễn Quang Huy (metrics/Ragas adapter) |
| Observability     | Cleaned/corrupted/repaired dataframe | Đếm null/duplicate/summary ngắn/stale row, đối chiếu corruption log với quality signal | `data/quality/*.json`, `data/results/corruption_log.json` join | Bùi Minh Long |
| Reporting         | Dict metrics/quality/freshness | Sinh Markdown report | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Bùi Minh Long |
| Corruption/repair | Cleaned dataframe | Drop/blank/noise/truncate/stale/duplicate (seed 42); repair bằng rebuild lại từ raw records | `data/clean/papers_clean_corrupted.*`, `data/clean/papers_clean_repaired.*` | Nguyễn Mai Huy |
| Orchestration     | Toàn bộ bước trên | Gọi đúng thứ tự qua `script/run_phase1.py`, `script/run_corruption_flow.py` | Baseline/corrupted/repaired metrics đầy đủ | Nguyễn Quang Huy |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`               | `gemini` |
| `LLM_MODEL`                  | `gemini-3.5-flash` |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 (`max_results = 24`) |
| Retrieval`top_k`             | 4 |
| Freshness threshold          | 180 ngày |
| Random seed, nếu có        | `RANDOM_SEED = 42` (corruption) |

Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

```bash
uv sync
```

### Lệnh chạy

Baseline:

```bash
uv run python script/run_phase1.py
```

Corruption flow (bao gồm repair):

```bash
uv run python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 2026-08-06 | `data/clean/papers_clean.json` (24 dòng), `data/results/baseline_metrics.json`, `data/quality/baseline_quality.json`, `data/reports/phase1_report.md` |
| Corruption flow   | Thành công (bao gồm repair) | 2026-08-06 | `data/results/corruption_log.json`, `corrupted_metrics.json`, `repaired_metrics.json`, `data/quality/corrupted_quality.json`, `repaired_quality.json`, `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref `/works` API |
| Query/filter                | `agentic retrieval augmented generation large language model`, filter `from-pub-date:<180 ngày trước>,has-abstract:true` |
| Số record nhận được    | 24 (24 API item → 24 parsed record → 24 clean record, không mất record, không DOI trùng) |
| Cơ chế retry/backoff      | Exponential backoff cho status tạm thời 429/500/502/503/504 |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` (DOI) | string | Có | Định danh tài liệu xuyên suốt pipeline (raw → clean → index → eval) | Loại record nếu null; loại duplicate theo `paper_id`, giữ bản ghi đầu |
| `title` | string | Có | Tiêu đề paper | Loại record nếu title < 3 ký tự |
| `summary` (abstract) | string | Có | Nội dung tóm tắt, dùng cho `text_for_embedding` | Loại record nếu summary < 20 ký tự |
| `published`/`published_dt` | string / datetime | Có | Ngày xuất bản, dùng tính `age_days` và freshness | Parse các dạng `YYYY`, `YYYY-MM`, `YYYY-MM-DD`; thiếu ngày/tháng mặc định = 1 |
| `categories`/`subject` | string | Không | Phân loại paper | Snapshot Crossref hiện thiếu 24/24 → `categories_joined` rỗng, câu hỏi loại `categories` được viết lại dựa theo `summary` |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Loại record title < 3 ký tự hoặc summary < 20 ký tự hoặc thiếu ngày published | Completeness/Validity | 0 (baseline snapshot không có record nào bị loại) | `baseline_quality.json`: `row_count = 24`, khớp raw 24 record |
| Loại duplicate theo `paper_id`, giữ bản đầu | Uniqueness | 0 ở baseline, 2 sau khi corruption chèn duplicate | `baseline_quality.json` (`duplicate_paper_ids = 0`) vs `corrupted_quality.json` (`= 2`) |
| Chuẩn hoá timezone khi tính `age_days` (`run_ts` về UTC-naive trước khi trừ `published_dt`) | Validity (tránh crash pipeline) | Toàn bộ 24 record | Smoke test: raw 24 → clean 24, `age_days` kiểu `int64`, không còn lỗi `TypeError: Cannot subtract tz-naive and tz-aware datetime-like objects` |

`text_for_embedding` được ghép từ `title` + `summary` sau khi chuẩn hoá whitespace, để index và retrieval dựa trên đúng nội dung đã làm sạch. `paper_id` lấy trực tiếp từ DOI gốc, không tự sinh ID mới, để `LocalEmbeddingIndex` và `test_set.json` (`ground_truth_doc_ids`) luôn tham chiếu cùng một khoá. `age_days` = `run_date - published_dt`, dùng làm input cho freshness check (ngưỡng 180 ngày).

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 20 (5 paper × 4 loại câu hỏi) |
| Các`question_type`                      | `authors`, `date`, `categories` (viết lại theo nội dung do thiếu `subject`), `summary` |
| Ground-truth document ID                 | `ground_truth_doc_ids = [row["paper_id"]]` lấy trực tiếp từ cleaned dataframe, không tự sinh ID |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection                  | ChromaDB, collection riêng cho baseline/corrupted/repaired |
| Retrieval`top_k`                         | 4 |
| LLM provider/model                       | `gemini` / `gemini-3.5-flash` |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` — cùng 20 câu hỏi cho baseline, corrupted, repaired |

Test set được giữ nguyên (cùng file, cùng `ground_truth`/`ground_truth_doc_ids`) khi đánh giá cả ba trạng thái, vì nếu mỗi trạng thái dùng câu hỏi khác nhau thì chênh lệch `retrieval_hit_rate`/`token_f1` giữa baseline/corrupted/repaired có thể do đổi câu hỏi chứ không phải do corruption/repair — làm mất tính so sánh được. Mỗi template câu hỏi (`authors`, `date`, `categories`, `summary`) được thiết kế khớp đúng logic từ khoá mà `qa.py::_extract_answer` dùng để chọn câu trả lời, để `ground_truth` phản ánh đúng cách hệ thống thật sự trả lời khi retrieval đúng.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế              | Trạng thái | Ghi chú   |
| ------------------------ | ------------------------------------ | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | 24 API item, 24 parsed record |
| Cleaned dataset          | `data/clean/papers_clean.csv/.json`  | Có | 24 dòng, `passed: true` |
| Embedding/index          | ChromaDB (baseline collection)       | Có | Build từ `text_for_embedding` |
| Evaluation set           | `data/eval/test_set.json`            | Có | 20 câu hỏi |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Xem bảng dưới |
| Quality/freshness        | `data/quality/baseline_quality.json`, `freshness_report.json` | Có | Pass / Fresh |
| Baseline report          | `data/reports/phase1_report.md`      | Có | Sinh từ đúng 3 JSON trên |

### Baseline metrics

| Metric               |       Giá trị | Diễn giải                             |
| -------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     1.0 | Toàn bộ 20 câu hỏi đều retrieve đúng `paper_id` |
| `mean_token_f1`      |     1.0 | Answer khớp hoàn toàn `ground_truth` (token-level) |
| `judge_accuracy`     |     1.0 | LLM judge đánh giá đúng 100% câu trả lời |
| `mean_judge_score`   |     5.0 | Điểm tuyệt đối trên thang 1–5 |
| Ragas | `context_precision = 0.50`, `context_recall = 0.50`, `faithfulness = 0.4875` | Dù exact-match QA đạt tối đa, top-k context vẫn còn lẫn nội dung không liên quan (precision/recall chỉ ~0.5), cho thấy retrieval "đúng doc" nhưng chưa "chỉ đúng doc" |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| `paper_id_nulls`, `title_nulls` | Completeness | = 0 | 0 / 0 | `baseline_quality.json` |
| `duplicate_paper_ids` | Uniqueness | = 0 | 0 | `baseline_quality.json` |
| `summary_too_short` | Validity | = 0 (< 20 ký tự bị loại từ cleaning) | 0 | `baseline_quality.json` |
| `stale_rows` (theo `age_days` > 180) | Timeliness | = 0 | 0 | `baseline_quality.json`, `freshness_report.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Cleaned dataset (`data/clean/papers_clean.json`) |
| Timestamp mới nhất       | `latest_published = 2026-08-01`, `oldest_published = 2026-02-12` |
| Ngưỡng freshness         | 180 ngày (`freshness_threshold_days`) |
| Trạng thái baseline      | Fresh (`is_fresh: true`, 0/24 stale) |
| Lý do                     | Toàn bộ 24 record có `published` trong vòng 180 ngày gần nhất so với thời điểm chạy pipeline |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Drop 3 record mới nhất | Xoá `n` dòng đầu sau khi sort theo `published` giảm dần | 3 | `row_count` giảm | `row_count` 24→23; là nguyên nhân chính làm `retrieval_hit_rate` giảm (3/5 paper trong test set bị xoá hẳn khỏi index) | Rebuild lại từ `crossref_records.json` gốc |
| Blank summary | Xoá nội dung `summary` | 3 | `summary_too_short` tăng | `summary_too_short` 0→4 | Rebuild từ raw |
| Truncate title | Cắt ngắn `title` | 3 | Không có check nào bắt trực tiếp (`title_nulls` vẫn 0 vì title chỉ ngắn, không null) | Không đổi tín hiệu quality nào đo được | Rebuild từ raw |
| Inject noise vào summary | Thêm ký tự nhiễu vào `summary` | 3 | Không có check đo noise text trong repo | Không đổi tín hiệu quality nào đo được | Rebuild từ raw |
| Làm stale date | Đặt `published` về quá khứ xa (vd. 2010-01-01) | 3 | `stale_rows` tăng | `stale_rows` 0→3, `is_fresh` true→false | Rebuild từ raw |
| Duplicate 2 record | Nhân bản `paper_id` đã có | 2 | `duplicate_paper_ids` tăng | `duplicate_paper_ids` 0→2 | Rebuild từ raw (loại duplicate lại theo `paper_id`) |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log đủ 6 loại corruption, liệt kê rõ `paper_id` từng record bị tác động (`dropped_latest_paper_ids`, `blanked_summary_paper_ids`, `noise_injected_paper_ids`, `truncated_title_paper_ids`, `stale_date_paper_ids`, `duplicated_paper_ids`) và `RANDOM_SEED = 42` để tái lập được.

Repair đọc lại `data/raw/crossref_records.json` (raw records gốc, không đụng tới dữ liệu đã bị corrupt) rồi chạy lại đúng `cleaning.py` để tạo `data/clean/papers_clean_repaired.*` — nghĩa là phục hồi bằng cách dựng lại dữ liệu từ nguồn đáng tin cậy, không phải sửa đè hoặc che giấu các dòng lỗi trong bản corrupted. Vì vậy `repaired_quality.json`/`freshness_repaired.json` giống hệt baseline (24 dòng, 0 vi phạm) thay vì chỉ "giảm số lỗi".

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`     |     1.0 |      0.4 |      1.0 | -0.6 | 100% | Phục hồi hoàn toàn về mức baseline |
| `mean_token_f1`          |     1.0 |     0.307 |      1.0 | -0.693 | 100% | Nhất quán với retrieval phục hồi |
| `judge_accuracy`         |     1.0 |      0.4 |      1.0 | -0.6 | 100% | Judge xác nhận tác động và phục hồi rõ ràng |
| `mean_judge_score`       |     5.0 |      2.9 |      5.0 | -2.1 | 100% | Về đúng thang điểm tuyệt đối |
| Quality checks pass/fail | Pass |      Fail |     Pass | 2 duplicate, 4 summary ngắn, 3 stale, row_count 24→23 | 100% | `repaired_quality.json` giống hệt baseline |
| Freshness status         |    Fresh | Not fresh |    Fresh | `stale_rows` 0→3, `is_fresh` true→false | 100% | `freshness_repaired.json` giống hệt baseline |

Hai kết luận nhân quả có bằng chứng từ artifact:

1. **Corruption** (drop 3 record mới nhất + blank summary + duplicate + stale date, seed 42) → **quality/freshness signal đổi rõ**: `row_count` 24→23, `duplicate_paper_ids` 0→2, `summary_too_short` 0→4, `stale_rows` 0→3, `passed`/`is_fresh` true→false (nguồn: `corrupted_quality.json`, `freshness_corrupted.json`) → **agent metric giảm mạnh**: `retrieval_hit_rate` 1.0→0.4, `mean_judge_score` 5.0→2.9 (nguồn: `corrupted_metrics.json`, cùng `test_set.json` với baseline). Đối chiếu `ground_truth_doc_ids` của test set với `corruption_log.json` cho thấy 3/5 paper được lấy mẫu bị **drop hẳn khỏi index** (12/20 câu hỏi liên quan) — đây là nguyên nhân chính của việc retrieval giảm 60 điểm phần trăm, nhiều hơn phần đóng góp của blank/truncate/noise.
2. **Repair** (rebuild lại từ `crossref_records.json` gốc, chạy lại `cleaning.py`) → **quality/freshness signal quay lại pass/fresh giống hệt baseline** (`repaired_quality.json`, `freshness_repaired.json`) → **agent metric phục hồi hoàn toàn về baseline**: `retrieval_hit_rate`/`mean_token_f1`/`judge_accuracy`/`mean_judge_score` đều bằng đúng giá trị baseline trong `repaired_metrics.json`.

Không có kết luận nào bị suy diễn thiếu bằng chứng: hai loại corruption `truncated_title_paper_ids` và `noise_injected_paper_ids` không làm đổi bất kỳ quality signal nào đo được trong repo (không có check đo độ dài title tối thiểu sau cleaning hay noise text), nên nhóm không kết luận rằng quality check "bắt được toàn bộ" 6 loại corruption — chỉ 4/6 loại có tín hiệu thay đổi rõ trong `data/quality/`.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Chạy lại `cleaning.py` báo lỗi `TypeError: Cannot subtract tz-naive and tz-aware datetime-like objects` khi tính `age_days`.
- **Nguyên nhân:** `now_utc()` (`src/core/utils.py`) trả về datetime UTC-aware, trong khi `published_dt` được parse từ Crossref là datetime timezone-naive; pandas không cho phép trừ trực tiếp hai loại này.
- **Cách xử lý:** Chuẩn hoá `run_ts` về UTC-naive ngay trước khi trừ với `published_dt`, giữ nguyên contract UTC của `now_utc()` ở phía gọi và giới hạn thay đổi trong bước cleaning (không sửa `now_utc()` để tránh ảnh hưởng module khác đang dùng nó).
- **Cách xác minh:** `python script/run_phase1.py` chạy lại thành công, smoke test cleaning cho ra đúng 24/24 record với `age_days` kiểu `int64`; `data/clean/papers_clean.json` khớp byte-for-byte khi diff lại từ dữ liệu Crossref thật.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Crossref snapshot thiếu hoàn toàn trường `subject` (24/24 record) | Câu hỏi loại `categories` không có ground truth category thật, phải viết lại dựa theo nội dung summary | Thử filter/query Crossref khác để lấy nguồn có `subject`, hoặc tự gắn cờ rõ trong `test_set.json` khi category bị suy ra thay vì lấy trực tiếp từ metadata |
| `build_test_set` lấy mẫu bằng `df.head(SAMPLE_SIZE)` sau khi `cleaning.py` sort theo `published` giảm dần, trùng hướng ưu tiên với `corrupt_clean_dataframe`'s drop-latest | Test set thiên vị theo cùng trục thời gian với corruption (3/5 paper mẫu bị corruption drop), phóng đại mức giảm `retrieval_hit_rate` đo được so với mức trung bình toàn dataset | Đổi sang `df.sample(SAMPLE_SIZE, random_state=...)` với seed cố định; đo lại tỷ lệ overlap giữa `ground_truth_doc_ids` và `corruption_log.json` qua nhiều seed, kỳ vọng dao động quanh tỷ lệ drop thật (không cố định cao như hiện tại) |
| 2 loại corruption (`truncated_title_paper_ids`, `noise_injected_paper_ids`) không có quality check nào đo được | Report không thể khẳng định quality check bao phủ mọi loại lỗi dữ liệu, dễ gây hiểu nhầm nếu không nêu rõ | Thêm check độ dài `title` tối thiểu và một signal đo mật độ ký tự bất thường trong `summary`, sau đó chạy lại corruption flow để xác nhận 6/6 loại đều có tín hiệu |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
