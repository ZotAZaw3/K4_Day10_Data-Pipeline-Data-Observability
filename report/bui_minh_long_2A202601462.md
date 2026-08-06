# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Bùi Minh Long             |
| MSSV               | 2A202601462                     |
| Khóa/Lớp         | K4              |
| Tên nhóm         | [Tên hoặc mã nhóm]     |
| Vai trò chính    | Evaluation & Observability owner |
| Repository         | https://github.com/ZotAZaw3/K4_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Evaluation set builder | `src/evaluation/testset.py` — `build_test_set(df, output_path)` | Cleaned dataframe (`paper_id`, `title`, `summary`, `authors_joined`, `categories_joined`, `published`) | `data/eval/test_set.json` — 20 câu hỏi thật (5 paper × 4 loại) sinh từ dữ liệu Crossref đã clean | Hoàn thành, **đã chạy trên dữ liệu Crossref thật** qua `script/run_phase1.py` |
| Data quality checks | `src/observability/quality.py` — `run_data_quality_checks(df, settings, report_name)` | Cleaned dataframe | `data/quality/baseline_quality.json` (row count, null, duplicate, stale rows) | Hoàn thành, đã chạy trên `data/clean/papers_clean.json` thật (24 dòng, `passed: true`) |
| Freshness report | `src/observability/quality.py` — `build_freshness_report(df, settings, report_path)` | Cleaned dataframe (`published`, `age_days`) | `data/quality/freshness_report.json` (`latest_published`, `oldest_published`, `stale_rows`, `is_fresh`) | Hoàn thành, đã chạy; `is_fresh: true`, 0 stale rows |
| Markdown reporting | `src/observability/reporting.py` — `generate_phase1_report(...)`, `generate_corruption_report(...)` | Dict `metrics`/`quality`/`freshness` từ các bước trên | `data/reports/phase1_report.md` (đã sinh, khớp JSON/CSV thật) | `generate_phase1_report` hoàn thành và đã chạy thật; `generate_corruption_report` mới self-check — chưa đủ input vì `repaired_metrics.json` chưa tồn tại |
| Corrupted dataset quality/freshness + join với corruption log | `src/pipelines/corruption_quality_flow.py` — `main()`, `src/observability/correlation.py` — `correlate_corruption_with_quality(...)` | Corrupted dataframe (từ `corrupt_clean_dataframe`), `corruption_log.json`, baseline `quality`/`freshness` JSON có sẵn trong `data/quality/` | `data/quality/corrupted_quality.json`, `data/quality/freshness_corrupted.json`, `data/quality/corruption_quality_correlation.json` | Hoàn thành, **đã chạy trên dữ liệu thật** (`data/clean/papers_clean.json`, 24 dòng) — 2026-08-06 |

Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

**Cập nhật checkpoint 3 (2026-08-06):** `cleaning.py` và `phase1.py` đã được implement và chạy end-to-end thành công qua `script/run_phase1.py` — 24 raw records → 24 clean rows → Chroma index → 20 câu hỏi eval → `baseline_metrics.json`/`baseline_quality.json`/`freshness_report.json`/`phase1_report.md`. Tôi đã tự chạy lại `run_data_quality_checks`, `build_freshness_report`, `generate_phase1_report` trên đúng `data/clean/papers_clean.json` hiện có trong repo và diff byte-for-byte với các file đã tồn tại — output giống hệt, xác nhận report không bị lệch khỏi dữ liệu thật. Phần việc của tôi giờ có bằng chứng end-to-end cho baseline, không còn dừng ở unit-level self-check nữa.

`corruption_flow.py` đã tạo được `corrupted_metrics.json`/`corrupted_quality.json` (dùng đúng hàm `run_data_quality_checks` tôi viết, schema khớp) nhưng chưa có bước repair (`repaired_metrics.json` chưa tồn tại), nên `generate_corruption_report` vẫn chưa chạy được đủ input — xem mục 8.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Đọc `retrieval/qa.py` và `retrieval/index.py` để suy ra contract câu hỏi/metadata | RAG & agent owner | Xác nhận `question_type` và cách `answer_question` trích câu trả lời, tránh test set và agent lệch format nhau |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Implement `build_test_set` | `src/evaluation/testset.py` | Hàm sinh 4 câu hỏi/paper, ghi JSON qua `write_json` | `python src/evaluation/testset.py` (self-check `assert`, dùng dataframe giả lập trong `tempfile`) |
| Implement `run_data_quality_checks` + `build_freshness_report` | `src/observability/quality.py` | Hai hàm trả dict + ghi JSON | `python src/observability/quality.py` (self-check `assert`) |
| Implement `generate_phase1_report` + `generate_corruption_report` | `src/observability/reporting.py` | Hai hàm ghi Markdown từ dict metrics/quality/freshness | `python src/observability/reporting.py` (self-check `assert`) |
| Chạy quality/freshness cho corrupted dataset + join với corruption log | `src/pipelines/corruption_quality_flow.py`, `src/observability/correlation.py` | `data/quality/corrupted_quality.json`, `data/quality/freshness_corrupted.json`, `data/quality/corruption_quality_correlation.json` (trên dữ liệu Crossref thật) | `PYTHONPATH=src python script/run_corruption_quality_check.py` + self-check `python src/observability/correlation.py` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Mỗi file có một khối `_demo()`/`if __name__ == "__main__"` tự kiểm tra bằng `assert` trên dữ liệu giả lập (không đụng tới `data/` thật, dùng `tempfile.TemporaryDirectory`), vì tại thời điểm này chưa có cleaned dataframe thật để chạy full pipeline.

Output cụ thể (2026-08-06, `data/quality/corruption_quality_correlation.json`): với 24 paper gốc, corruption làm `row_count` 24→23, `summary_too_short` 0→4, `stale_rows` 0→3, `duplicate_paper_ids` 0→2 — cả bốn đều được gắn evidence (giá trị trước/sau + số dòng bị corrupt tương ứng) trong `changed_signals`. Đồng thời `unchanged_signals` ghi rõ `truncated_title_paper_ids` (3 dòng) không làm `title_nulls` đổi (vẫn 0) và `noise_injected_paper_ids` (3 dòng) không có signal nào trong repo đo được — để không kết luận quá mức rằng mọi loại corruption đều bị quality check bắt được.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Phần của tôi giải quyết ba việc trong pipeline: (1) tạo bộ câu hỏi đánh giá (`test_set.json`) có `ground_truth` kiểm chứng được, (2) đo chất lượng/độ mới của dữ liệu clean bằng số liệu cụ thể thay vì cảm tính, (3) gói các số liệu đó thành báo cáo Markdown để người khác đọc mà không cần mở JSON.

### Cách triển khai

**1) Đọc `testset.py`, `qa.py`, `metrics.py` để hiểu format answer/metric.**
`retrieval/qa.py::answer_question` trả về `AnswerResult(answer, retrieved_doc_ids, retrieved_contexts, retrieved_titles)`. Điểm quan trọng: `_extract_answer` chọn câu trả lời bằng cách match từ khóa trong câu hỏi — `"who authored"/"list the authors"` → `authors_joined`, `"when was"/"publication date"/"published on"` → `published`, `"what categories"` → `categories_joined`, còn lại → câu đầu tiên của `summary`. Ngoài ra nếu câu hỏi chứa title trong dấu nháy đơn (`'...'`), `answer_question` sẽ `index.lookup()` chính xác paper đó trước khi search. `evaluation/metrics.py::evaluate_pipeline` đọc `test_set.json`, gọi `answer_question`, rồi so `result.retrieved_doc_ids` với `item["ground_truth_doc_ids"]` để tính `retrieval_hit_rate`, và so `item["ground_truth"]` với `result.answer` để tính `token_f1`/judge score.

**2) Thiết kế câu hỏi summary/authors/date/categories từ dữ liệu thật.**
Vì `_extract_answer` chọn nhánh trả lời dựa theo từ khóa trong câu hỏi, tôi viết 4 template câu hỏi cố định, mỗi loại chứa đúng từ khóa `_extract_answer` cần và luôn kèm title paper trong dấu nháy đơn để kích hoạt exact lookup:

- `authors`: `"Who authored the paper '{title}'?"` → ground truth = `row["authors_joined"]`
- `date`: `"When was the paper '{title}' published?"` → ground truth = `row["published"]`
- `categories`: `"What categories does the paper '{title}' belong to?"` → ground truth = `row["categories_joined"]`
- `summary`: `"What is the paper '{title}' about?"` (không khớp từ khóa nào ở trên nên rơi vào nhánh mặc định) → ground truth = `first_sentence(row["summary"])`

Nhờ vậy `ground_truth` luôn khớp chính xác với những gì `answer_question` sẽ trả về khi retrieval đúng — nếu sai lệch là do retrieval kém, không phải do ground truth viết sai.

**3) `ground_truth_doc_ids` lấy từ `paper_id` clean, không tự bịa ID.**
Mỗi row lấy trực tiếp `row["paper_id"]` (cột do `cleaning.py` sinh ra) bọc trong list 1 phần tử: `"ground_truth_doc_ids": [row["paper_id"]]`. Tôi không tạo ID mới hay đoán ID — vì `LocalEmbeddingIndex` dùng đúng `paper_id` này làm `SearchResult.paper_id`, nên nếu test set tự bịa ID khác, `retrieval_hit_rate` sẽ luôn sai dù retrieval đúng.

**4) Join corruption log với quality signal — chỉ báo "đổi" khi có bằng chứng (2026-08-06).**
`correlate_corruption_with_quality` (trong `src/observability/correlation.py`) nhận `corruption_log.json` cùng 4 báo cáo baseline/corrupted quality+freshness, và có một bảng ánh xạ cố định `CORRUPTION_SIGNAL_MAP` nối mỗi loại corruption với đúng một field quality/freshness *có khả năng* bắt được nó (vd. `blanked_summary_paper_ids` → `quality.summary_too_short`, `stale_date_paper_ids` → `freshness.stale_rows`). Với mỗi loại corruption có ID bị ảnh hưởng (`affected_count > 0`), hàm so `baseline_value` với `corrupted_value` của field đó:
- Nếu khác nhau → xếp vào `changed_signals` kèm `evidence` (giá trị trước/sau + số dòng bị corrupt).
- Nếu giống nhau, hoặc corruption đó không có field nào ánh xạ tới (`mapping is None`, ví dụ `noise_injected_paper_ids` — repo chưa có check nào đo noise text) → xếp vào `unchanged_signals` kèm lý do cụ thể.

Cách làm này tránh hai lỗi thường gặp: (a) suy diễn "corruption chạy rồi thì coi như mọi metric liên quan đã tệ đi" mà không kiểm tra số thật, và (b) im lặng bỏ qua các loại corruption không có signal nào bắt được — khiến người đọc report tưởng nhầm là quality check đã bao phủ hết mọi rủi ro.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Cleaned dataframe với cột `paper_id, title, summary, authors_joined, categories_joined, published, age_days` (do `cleaning.py` bàn giao); riêng `correlate_corruption_with_quality` nhận thêm `corruption_log.json` + 4 dict quality/freshness (baseline, corrupted) |
| Output                         | `data/eval/test_set.json` (list dict), `data/quality/<name>.json`, `data/quality/freshness_report.json`, `data/reports/phase1_report.md`, `data/reports/corruption_report.md`, `data/quality/freshness_corrupted.json`, `data/quality/corruption_quality_correlation.json` |
| Module phụ thuộc             | `ingestion/cleaning.py` (schema), `ingestion/corruption.py` (`corrupt_clean_dataframe`, sinh `corruption_log.json`), `core/utils.py` (`write_json`, `write_text`, `first_sentence`, `read_json`), `core/config.py` (`Settings.paths`, `freshness_threshold_days`) |
| Module sử dụng output        | `evaluation/metrics.py` (đọc `test_set.json`), `pipelines/phase1.py` và `pipelines/corruption_flow.py` (gọi quality/freshness/reporting), `pipelines/corruption_quality_flow.py` (gọi `correlate_corruption_with_quality`) |
| Điều kiện lỗi cần xử lý | Dataframe rỗng → `build_test_set` raise `ValueError` thay vì ghi test set rỗng; thiếu cột `age_days` → quality/freshness fallback `stale_rows = 0` thay vì crash; corruption type không có mapping quality/freshness → xếp vào `unchanged_signals` thay vì bỏ sót âm thầm |

### Cách xác minh

```bash
PYTHONPATH=src python src/evaluation/testset.py
PYTHONPATH=src python src/observability/quality.py
PYTHONPATH=src python src/observability/reporting.py
PYTHONPATH=src python src/observability/correlation.py
PYTHONPATH=src python script/run_corruption_quality_check.py
```

- **Kết quả mong đợi:** mỗi lệnh in ra dòng `... self-check OK`, không có `AssertionError`/traceback; riêng `run_corruption_quality_check.py` in ra log số signal đổi/không đổi.
- **Kết quả thực tế:** cả bốn lệnh self-check chạy OK trên dữ liệu giả lập trong `tempfile`.
- **Artifact/log (cập nhật checkpoint 3):** `phase1.py` đã chạy thật qua `script/run_phase1.py` và gọi đúng ba hàm này — `data/eval/test_set.json`, `data/quality/baseline_quality.json`, `data/quality/freshness_report.json`, `data/reports/phase1_report.md` đều tồn tại. Tôi chạy lại `run_data_quality_checks`/`build_freshness_report`/`generate_phase1_report` trực tiếp trên `data/clean/papers_clean.json` hiện có và diff với các file trên bằng `diff` — kết quả **giống hệt (identical)**, xác nhận report không lệch khỏi dữ liệu thật.
- **Artifact/log (cập nhật 2026-08-06):** `PYTHONPATH=src python script/run_corruption_quality_check.py` chạy thật trên `data/clean/papers_clean.json` (24 paper), log ra `INFO:pipelines.corruption_quality_flow:Corrupted quality/freshness reports written to .../data/quality. 4 signal(s) changed with evidence, 2 unchanged.` — khớp đúng số lượng entry trong `data/quality/corruption_quality_correlation.json` (`changed_signals` có 4 phần tử, `unchanged_signals` có 2 phần tử).

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn cách viết câu hỏi trong `build_test_set` sao cho `ground_truth` chắc chắn đúng mà không cần LLM chấm điểm.
- **Các phương án đã cân nhắc:** (1) Dùng LLM sinh câu hỏi tự do từ `summary` — đa dạng hơn nhưng `ground_truth` khó kiểm chứng bằng string match và tốn API call khi build test set. (2) Viết câu hỏi theo template cố định, khớp đúng logic từ khóa của `_extract_answer` trong `qa.py`.
- **Phương án đã chọn:** (2) — template cố định.
- **Lý do:** `metrics.py` so sánh `ground_truth` với `result.answer` bằng token-F1/LLM judge; nếu ground truth không khớp cách `qa.py` thực sự trả lời (dù retrieval đúng 100%) thì metric sẽ phản ánh sai lỗi ground-truth-mismatch thay vì lỗi retrieval thật. Template cố định loại bỏ nguồn nhiễu này, và không tốn LLM call khi build test set (chỉ cần cleaned dataframe).
- **Bằng chứng quyết định phù hợp:** Self-check trong `testset.py::_demo()` dựng 1 paper giả lập và assert `ground_truth` của từng `question_type` khớp chính xác với field tương ứng (`authors_joined`, `published`, `categories_joined`, `first_sentence(summary)`).

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Không phải lỗi runtime — mà là rủi ro thiết kế: nếu viết câu hỏi tự do (vd. "Summarize this paper"), `ground_truth` sẽ không khớp cách `_extract_answer` chọn câu trả lời, khiến `token_f1`/`judge_accuracy` thấp dù retrieval đúng.
- **Lệnh hoặc bước tái hiện:** Đọc `src/retrieval/qa.py::_extract_answer` và thử map từng loại câu hỏi dự kiến vào các nhánh `if/elif` của hàm đó.
- **Nguyên nhân gốc:** `testset.py` và `qa.py` là hai module độc lập nhưng phải đồng thuận ngầm về format câu hỏi/câu trả lời; không có schema/interface chung ràng buộc điều này.
- **Cách xử lý:** Viết 4 template câu hỏi bám sát đúng từ khóa mà `_extract_answer` nhận diện (`"who authored"`, `"when was"`, `"what categories"`, và nhánh mặc định cho summary), đồng thời luôn kèm title trong dấu nháy đơn để tận dụng exact lookup.
- **Cách xác minh sau khi sửa:** `testset.py::_demo()` assert từng `ground_truth` khớp field dữ liệu; khi chạy full pipeline sau này sẽ đối chiếu thêm bằng `retrieval_hit_rate`/`token_f1` trong `baseline_metrics.json`.
- **Điều học được:** Contract giữa các module không chỉ nằm ở tên field/tham số hàm, mà còn ở logic ẩn bên trong (ở đây là cách `_extract_answer` phân nhánh theo từ khóa câu hỏi) — phải đọc code thật của module tiêu thụ output, không chỉ đọc docstring.

**Cập nhật checkpoint 3 — baseline đã xử lý xong:** `cleaning.py` và `phase1.py` đã được implement (không còn `NotImplementedError`) và `script/run_phase1.py` đã chạy thành công, sinh đủ `test_set.json`, `baseline_quality.json`, `freshness_report.json`, `phase1_report.md`, `baseline_metrics.json` trên dữ liệu Crossref thật (24 records). `data/eval/test_set.json` đã được kiểm tra: toàn bộ 20 `ground_truth_doc_ids` đều tồn tại trong `paper_id` của `data/clean/papers_clean.json`, không có ID mồ côi.

Phần còn lại chưa xử lý xong (không phải do module của tôi):

- **Phạm vi bị ảnh hưởng:** `generate_corruption_report` chưa chạy được với artifact thật vì `data/results/repaired_metrics.json` chưa tồn tại — `corruption_flow.py` mới dừng ở bước corrupt + evaluate corrupted, chưa chạy bước repair.
- **Những gì đã loại trừ:** Đã xác nhận `corrupted_metrics.json`/`corrupted_quality.json` tồn tại và đúng schema (do hàm `run_data_quality_checks` của tôi sinh ra), nên nghẽn không nằm ở phía observability mà ở bước repair chưa được gọi trong `corruption_flow.py`.
- **Bước tiếp theo:** Khi `repaired_metrics.json`/`repaired_quality`/`freshness_repaired.json` xuất hiện, gọi `generate_corruption_report` với đủ 7 tham số rồi đối chiếu `data/reports/corruption_report.md` với 3 bộ JSON đó, tương tự cách đã làm với `phase1_report.md`.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

**Câu trả lời:**

1. `crossref.py` fetch raw response từ Crossref API rồi parse thành `PaperRecord`, lưu vào `data/raw/`. `cleaning.py` chuẩn hoá các record đó thành dataframe (`paper_id`, `text_for_embedding`, `age_days`, ...), lưu `data/clean/`. `LocalEmbeddingIndex.build()` đọc dataframe clean, embed `text_for_embedding` bằng MiniLM, và nạp vào một collection Chroma — mỗi document giữ `paper_id` gốc trong metadata để truy vết ngược lại clean data.
2. `build_test_set` (phần tôi phụ trách) sinh câu hỏi trực tiếp từ cleaned dataframe và gắn `ground_truth_doc_ids = [paper_id]` lấy nguyên từ dòng dữ liệu đó — không tạo ID mới. Khi evaluate, `answer_question` trả về `retrieved_doc_ids` từ kết quả search trên index; `evaluate_pipeline` so `retrieved_doc_ids` với `ground_truth_doc_ids` để tính `retrieval_hit_rate`, và so `answer` với `ground_truth` (string) để tính `token_f1`/judge score — nên "đúng" ở đây nghĩa là index trả về đúng paper gốc và nội dung trả lời khớp field thật của paper đó.
3. Quality checks (`run_data_quality_checks`) trả lời câu hỏi "dữ liệu có sạch không" tại một thời điểm cố định — đếm null, duplicate `paper_id`, title thiếu, summary quá ngắn. Freshness monitoring (`build_freshness_report`) trả lời câu hỏi khác: "dữ liệu có còn mới không" — dựa vào `published`/`age_days` so với `freshness_threshold_days`, không quan tâm dữ liệu có sạch hay không (một dataset có thể sạch nhưng vẫn cũ, hoặc mới nhưng có duplicate).
4. Baseline, corrupted, repaired phải dùng chung một `test_set.json` vì nếu mỗi trạng thái có câu hỏi/ground-truth-doc-id khác nhau thì chênh lệch `retrieval_hit_rate`/`token_f1` giữa ba trạng thái có thể do đổi câu hỏi chứ không phải do corruption/repair — làm mất tính so sánh được (điều `corruption_flow.py` cần để chứng minh nhân quả corruption → metric xấu đi → repair → metric phục hồi).
5. Repair được coi là thành công khi: (a) `repaired_metrics.json` có `retrieval_hit_rate`/`token_f1`/`judge_accuracy` gần trở lại mức baseline (đo trên cùng test set), và (b) `data/quality/`+`freshness_report.json` của repaired dataset không còn các vi phạm mà bản corrupted có (null/duplicate/stale) — nếu chỉ metric phục hồi mà quality signal vẫn xấu (hoặc ngược lại), phải nêu rõ là phục hồi chưa hoàn toàn, không được kết luận "đã sửa xong".

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |  **1.0** |  **0.4** |  Chưa chạy | Giảm 60 điểm phần trăm sau corruption; `repaired_metrics.json` chưa tồn tại nên chưa đo được mức phục hồi |
| `mean_token_f1`      |  **0.75** |  **0.254** |  Chưa chạy | Giảm gần 1/3; nhất quán với retrieval tệ đi (không tìm đúng doc thì answer khó khớp ground truth) |
| `judge_accuracy`     |  **0.75** |  **0.25** |  Chưa chạy | Giảm 50 điểm phần trăm |
| `mean_judge_score`   |  **4** |  **2** |  Chưa chạy | Giảm nửa thang điểm 1–5 |
| Quality checks         |  **passed: true** (24 rows, 0 null, 0 dup, 0 stale) |  **passed: false** (23 rows, 2 dup `paper_id`, 4 summary quá ngắn, 3 stale) |  Chưa chạy | Quality check bắt được 4/6 loại corruption đã áp dụng (drop, blank summary, stale date, duplicate — xem `changed_signals` trong `corruption_quality_correlation.json`). **Không bắt được** `truncated_title_paper_ids` (`title_nulls` vẫn 0/0 vì title bị cắt ngắn chứ không null) và `noise_injected_paper_ids` (chưa có check nào đo noise text) — hai signal này nằm trong `unchanged_signals`, không được tính là "quality check phát hiện toàn bộ corruption" |
| Freshness status       |  **is_fresh: true** (0 stale/24) |  stale_rows tăng lên 3 (theo `corrupted_quality.json`; `freshness_corrupted.json` do teammate observability khác đối chiếu) |  Chưa chạy | Baseline fresh hoàn toàn; corruption cố ý làm cũ `published` ở một phần dữ liệu |

Số liệu baseline/corrupted lấy từ `data/results/baseline_metrics.json` và `data/results/corrupted_metrics.json` thật trong repo (không phải giả lập); tôi đối chiếu bằng cách đọc trực tiếp hai file JSON, không suy diễn.

### Kết luận từ số liệu

Chuỗi nhân quả #1 đã có bằng chứng thật; chuỗi #2 (repair) vẫn phải chờ vì `repaired_metrics.json` chưa được `corruption_flow.py` sinh ra:

1. **Corruption** (`corrupt_clean_dataframe`: blank summary, truncate title, làm cũ `published`, thêm duplicate, drop record mới nhất) → **quality/freshness signal đổi**: `row_count` 24→23, `duplicate_paper_ids` 0→2, `summary_too_short` 0→4, `stale_rows` 0→3, `passed` true→false (nguồn: `data/quality/corrupted_quality.json`, đối chiếu chi tiết trong `corruption_quality_correlation.json`) → **agent metric đổi**: `retrieval_hit_rate` 1.0→0.4, `mean_token_f1` 0.75→0.254, `judge_accuracy` 0.75→0.25, `mean_judge_score` 4→2 (nguồn: `data/results/corrupted_metrics.json`, cùng `test_set.json` với baseline).
2. **Repair** (re-run `cleaning.py` từ `data/raw/crossref_records.json`) → quality/freshness signal kỳ vọng quay lại 0 vi phạm → agent metric kỳ vọng phục hồi về gần baseline — **chưa kiểm chứng được**, vì `corruption_flow.py` mới chạy đến bước evaluate corrupted, chưa gọi bước repair.

Corruption nào ảnh hưởng rõ nhất và vì sao?

Đã kiểm tra trực tiếp bằng cách so `ground_truth_doc_ids` của `test_set.json` với từng danh sách `*_paper_ids` trong `data/results/corruption_log.json`:

| Corruption | Số paper trong test set (/5) bị ảnh hưởng |
| --- | ---: |
| `dropped_latest_paper_ids` (drop hẳn record) | **3/5** |
| `duplicated_paper_ids` | 2/5 |
| `blanked_summary_paper_ids` | 1/5 |
| `truncated_title_paper_ids` | 0/5 |
| `stale_date_paper_ids` | 0/5 |

**Drop record là corruption ảnh hưởng rõ nhất**: 3 trong 5 paper được `build_test_set` lấy mẫu (tức 12/20 câu hỏi) bị xoá hẳn khỏi corrupted dataset trước khi build index — với các paper đó, cả exact-lookup theo title lẫn semantic search trong `answer_question` đều không thể trả về đúng `paper_id` vì document không còn tồn tại trong collection. Đây là nguyên nhân chính khiến `retrieval_hit_rate` rơi từ 1.0 xuống 0.4 (60% suy giảm khớp gần đúng với tỷ lệ 3/5 paper bị mất khỏi index).

Kết quả nào khác với kỳ vọng ban đầu?

Ban đầu tôi dự đoán corruption sẽ chủ yếu làm nhiễu *nội dung câu trả lời* (blank summary, truncate title) hơn là làm *retrieval sai hẳn document*, vì `answer_question` có cơ chế exact-lookup theo title nên tưởng sẽ "chống chịu" được phần nào. Thực tế ngược lại: nguyên nhân chính là `corrupt_clean_dataframe`'s `DROP_LATEST_FRACTION` xoá đúng các paper *mới nhất* (`corrupted.head(n_drop)` sau khi `cleaning.py` đã sort theo `published` giảm dần) — và `build_test_set`'s `sample = df.head(SAMPLE_SIZE)` cũng ưu tiên lấy các paper mới nhất làm mẫu. Hai lựa chọn thiết kế độc lập (của tôi và của người viết `corruption.py`) vô tình cùng "thiên vị" nhóm paper mới nhất, khiến tỷ lệ overlap cao hơn ngẫu nhiên — một rủi ro tôi không lường trước khi viết `build_test_set` chỉ với `df.head()`.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Test set cho RAG evaluation không thể viết tách rời khỏi cách hệ thống trả lời (`qa.py`) — ground truth phải khớp logic thật của answer extractor, không chỉ khớp "ý nghĩa" câu hỏi.
2. Quality (dữ liệu sạch) và freshness (dữ liệu mới) là hai trục độc lập, cần hai loại check riêng — gộp chung dễ che lấp vấn đề (dataset có thể pass quality nhưng stale, hoặc ngược lại).
3. Cách lấy mẫu để build test set không "trung lập" như tưởng: `sample = df.head(SAMPLE_SIZE)` của tôi và `DROP_LATEST_FRACTION` của `corruption.py` cùng ưu tiên nhóm paper mới nhất một cách độc lập, khiến 3/5 paper trong test set bị corruption xoá hẳn — test set thiên vị theo cùng một trục (thời gian) với corruption sẽ phóng đại tác động đo được thay vì phản ánh đúng mức độ corruption trung bình trên toàn dataset.

### Nếu có thêm thời gian

Đổi `build_test_set` từ `df.head(SAMPLE_SIZE)` sang lấy mẫu ngẫu nhiên có seed cố định (`df.sample(SAMPLE_SIZE, random_state=...)`) để tránh thiên vị theo thứ tự sort của `cleaning.py` (hiện đang sort theo `published` giảm dần) — đo cải thiện bằng cách so tỷ lệ overlap giữa `ground_truth_doc_ids` và từng danh sách `*_paper_ids` trong `corruption_log.json` qua vài lần chạy corruption khác seed, kỳ vọng tỷ lệ overlap dao động ngẫu nhiên quanh 15% (đúng bằng `DROP_LATEST_FRACTION`) thay vì cố định ở mức cao như hiện tại.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu (phần chưa chạy được đã ghi rõ "Chưa chạy" thay vì bịa số).
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Bùi Minh Long
**Ngày xác nhận:** 2026-08-06
