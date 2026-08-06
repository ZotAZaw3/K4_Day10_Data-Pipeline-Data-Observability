# Báo cáo cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Nguyễn Quang Huy |
| MSSV | 2A202601120 |
| Khóa/Lớp | K4 |
| Tên nhóm | Chưa cung cấp |
| Vai trò chính | Pipeline integration, evaluation và debugging |
| Repository | `K4_Day10_Data-Pipeline-Data-Observability` |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Evaluation set và golden answer | `data/eval/test_set.json`, `src/evaluation/testset.py` | Clean dataset | 20 evaluation samples có `ground_truth` và `ground_truth_doc_ids` | Hoàn thành artifact; generator còn cần cải thiện cho category |
| Evaluation metrics và Ragas adapter | `src/evaluation/metrics.py` | Test set, index, answers | Baseline/corrupted/repaired metrics | Hoàn thành |
| Debugging dữ liệu thời gian | `src/ingestion/cleaning.py` | Raw records, `run_date` | `age_days` nhất quán | Hoàn thành |
| JSON artifact serialization | `src/core/utils.py` | DataFrame records có Timestamp | JSON dùng được cho pipeline tiếp theo | Hoàn thành |
| Evidence và blocker tracking | `blocker.md`, `data/reports/` | Metrics, quality và freshness artifacts | Log blocker, phase reports, corruption report | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

- Rà soát `corruption.py` và corruption flow theo các lỗi drop, blank, noise, truncate, stale date và duplicate.
- Kiểm tra tính nhất quán giữa baseline, corrupted và repaired artifacts.
- Phân tích kết quả retrieval, answer evaluation, data quality và freshness.

## 3. Kết quả đã thực hiện

| Nhiệm vụ | Bằng chứng | Kết quả |
|---|---|---|
| Sửa timezone khi tính `age_days` | `src/ingestion/cleaning.py` | Smoke test: raw 24, clean 24, `age_days` kiểu `int64` |
| Sửa ghi clean DataFrame ra JSON | `src/core/utils.py` | Serialize 24 records có `pandas.Timestamp` thành công |
| Sửa lỗi Ragas `EvaluationResult` | `src/evaluation/metrics.py` | Tổng hợp metric từ `result.scores`, không còn dùng `dict(result)` |
| Làm sạch evaluation set | `data/eval/test_set.json` | 20 samples, không còn `ground_truth` rỗng |
| Chạy baseline | `data/results/baseline_metrics.json` | Retrieval và answer metrics đạt 1.0 |
| Chạy corruption và repair | `data/results/corruption_log.json`, `corrupted_metrics.json`, `repaired_metrics.json` | Corruption làm giảm chất lượng; repair khôi phục baseline |

## 4. Giải thích kỹ thuật

### 4.1. Sửa lỗi timezone

`now_utc()` trả về datetime có timezone UTC, trong khi ngày publication từ Crossref là datetime không có timezone. Pandas không cho phép trừ hai loại này trực tiếp.

Giải pháp được chọn là chuyển `run_ts` về UTC-naive ngay trước khi tính `age_days`. Cách này giữ nguyên contract UTC của `now_utc()` và giới hạn thay đổi trong bước cleaning.

### 4.2. Sửa lỗi JSON serialization

Clean DataFrame có các cột `published_dt` và `updated_dt` kiểu `pandas.Timestamp`. `json.dumps()` mặc định không hiểu kiểu này.

`write_json()` được bổ sung serializer chuyển datetime/date/Timestamp thành chuỗi ISO 8601. Nhờ đó clean, corrupted và repaired JSON dùng chung một cách ghi artifact.

### 4.3. Sửa lỗi Ragas

Ragas 0.4.3 trả về `EvaluationResult`, không phải dictionary. Việc gọi `dict(result)` gây lỗi `KeyError: 0`, được ghi thành `Ragas evaluation failed: 0`.

Giải pháp là đọc `result.scores`, tính trung bình từng metric, chuyển về `float` và bỏ giá trị không hữu hạn trước khi ghi JSON.

### 4.4. Điều chỉnh evaluation set

Crossref snapshot hiện không có trường `subject`, nên 5 câu hỏi `categories` có golden answer rỗng. Các entry này được viết lại thành câu hỏi về vấn đề/phạm vi của paper và lấy câu đầu của summary làm `ground_truth`.

Đây là điều chỉnh trung thực theo dữ liệu thực tế, không tự bịa category. Nếu muốn tự động sinh lại test set trong tương lai, cần cập nhật `src/evaluation/testset.py` để bỏ qua hoặc đánh dấu rõ các trường category bị thiếu.

## 5. Cách xác minh

Các kiểm tra chính:

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

Các smoke test đã thực hiện kiểm tra:

- Cleaning không còn lỗi timezone và tạo đủ `age_days`.
- JSON serialization đọc lại được 24 clean records.
- Ragas result conversion trả về metric dạng số.
- Evaluation set có 20 samples, không có `ground_truth` rỗng hoặc ID trùng.

Artifact xác minh:

- `data/results/baseline_metrics.json`
- `data/results/corrupted_metrics.json`
- `data/results/repaired_metrics.json`
- `data/results/corruption_log.json`
- `data/quality/`
- `data/reports/phase1_report.md`
- `data/reports/corruption_report.md`

## 6. Một lỗi và blocker đã xử lý

### Lỗi timezone

- **Triệu chứng:** `Cannot compare tz-naive and tz-aware datetime-like objects`.
- **Nguyên nhân:** `run_date` có UTC timezone nhưng publication date không có timezone.
- **Cách xử lý:** Chuẩn hóa `run_ts` về UTC-naive trước phép trừ.
- **Kết quả:** Cleaning smoke test thành công với 24/24 records.

### Lỗi JSON

- **Triệu chứng:** `Object of type Timestamp is not JSON serializable`.
- **Nguyên nhân:** DataFrame chứa `pandas.Timestamp` khi ghi clean JSON.
- **Cách xử lý:** Bổ sung datetime serializer trong `write_json()`.
- **Kết quả:** JSON serialization smoke test thành công.

### Lỗi Ragas

- **Triệu chứng:** `Ragas evaluation failed: 0`.
- **Nguyên nhân:** Gọi `dict()` trên `EvaluationResult` của Ragas 0.4.3.
- **Cách xử lý:** Aggregate trực tiếp từ `result.scores`.
- **Kết quả:** Ragas metrics được ghi thành số trong baseline/corrupted/repaired results.

## 7. Hiểu biết về luồng end-to-end

1. Crossref trả raw response và raw records; cleaning chuẩn hóa records, tính freshness và tạo `text_for_embedding`.
2. MiniLM tạo embedding, ChromaDB lưu vector index; evaluation set giữ câu hỏi, golden answer và ID tài liệu đúng.
3. Evaluation đo riêng retrieval hit và chất lượng answer; quality/freshness checks kiểm tra dữ liệu trước và sau corruption.
4. Baseline, corrupted và repaired phải dùng cùng test set để delta metrics phản ánh tác động của dữ liệu, không phải khác biệt do câu hỏi.
5. Repair thành công khi quality/freshness trở lại trạng thái đạt và metrics phục hồi gần hoặc bằng baseline.

## 8. Phân tích kết quả

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
|---|---:|---:|---:|---|
| `retrieval_hit_rate` | 1.00 | 0.40 | 1.00 | Corruption làm mất hoặc làm nhiễu tài liệu đúng; repair phục hồi hoàn toàn |
| `mean_token_f1` | 1.00 | 0.3074 | 1.00 | Chất lượng answer giảm mạnh khi context bị hỏng |
| `judge_accuracy` | 1.00 | 0.40 | 1.00 | Judge xác nhận tác động rõ ràng của corruption |
| `mean_judge_score` | 5.0 | 2.9 | 5.0 | Điểm trung bình giảm từ tuyệt đối xuống mức trung bình |
| Quality checks | Pass | Fail | Pass | Corrupted có 2 duplicate ID và 4 summary quá ngắn |
| Freshness | Fresh | Not fresh | Fresh | Corrupted có 3 stale rows; repaired không còn stale row |

Baseline có 24/24 records clean, quality pass và freshness pass. Corruption tạo dataset 23 rows, gồm 3 rows bị drop, 2 duplicate IDs, 4 summary quá ngắn và 3 stale rows. Kết quả retrieval giảm từ 1.00 xuống 0.40, còn repair khôi phục về 1.00.

Chuỗi bằng chứng chính:

1. Corruption dữ liệu → quality/freshness fail → retrieval và answer metrics giảm.
2. Repair từ raw records → quality/freshness pass → các metric chính trở lại baseline.

Corruption ảnh hưởng rõ nhất đến việc drop latest records, blank/noise summary và truncate title vì các lỗi này làm mất hoặc thay đổi nội dung được dùng để retrieval. Duplicate và stale date chủ yếu được phát hiện bởi observability checks.

Ragas baseline có `context_precision` 0.50, `context_recall` 0.50 và `faithfulness` 0.4875; corrupted giảm lần lượt xuống 0.1333, 0.35 và 0.28125. Điều này cho thấy dù exact QA baseline đạt tốt, context top-k vẫn còn nhiễu và cần được tối ưu thêm.

## 9. Bài học và hướng cải thiện

1. Cần thống nhất timezone ngay tại boundary giữa source data và runtime timestamp.
2. Artifact serialization phải xử lý rõ các kiểu dữ liệu pandas trước khi pipeline chuyển sang bước tiếp theo.
3. Evaluation set chỉ đáng tin khi mọi golden answer đều có dữ liệu thực và không bị rỗng.
4. Retrieval hit 1.0 chưa đủ để kết luận RAG tốt; cần xem thêm precision, recall và faithfulness của context.
5. Corruption log và quality report giúp biến lỗi dữ liệu thành bằng chứng định lượng.

Nếu có thêm thời gian, nên cập nhật testset builder để tự động bỏ qua category thiếu dữ liệu, bổ sung validation cho clean contract và tối ưu top-k/context filtering trước khi gọi Ragas.

## 10. Cam kết của thành viên

- [x] Báo cáo phản ánh đúng phần việc và artifact đã kiểm chứng.
- [x] Có thể giải thích luồng end-to-end và các lỗi đã xử lý.
- [x] Các kết luận chính đều có metric hoặc artifact đối chiếu.
- [x] Không ghi API key, token hoặc secret vào báo cáo.
- [x] Báo cáo không sao chép nguyên văn báo cáo nhóm.

**Họ và tên:** Nguyễn Quang Huy  
**MSSV:** 2A202601120  
**Ngày xác nhận:** 2026-08-06
