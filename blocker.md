# Blocker Log

Tài liệu này ghi nhận các vấn đề có thể làm dừng pipeline, kèm bằng chứng và điều kiện đóng.

## BLOCKER-001 — Đối soát raw count → clean count

- **Trạng thái:** RESOLVED
- **Phạm vi:** Raw ingestion → cleaning
- **Mức độ:** Blocker đã đóng
- **Kết quả kiểm tra:**
  - `raw_count`: 24
  - `clean_count`: 24
  - `dropped_count`: 0
  - `drop_rate`: 0%
  - Raw `paper_id` unique: Có
  - Clean `paper_id` unique: Có
  - Trường bắt buộc trong clean output: Đầy đủ
- **Bằng chứng:**
  - `data/raw/crossref_records.json`
  - `data/clean/papers_clean.csv`
  - `data/clean/papers_clean.json`
- **Điều kiện đóng:** Đã đạt. Raw và clean đã được đối soát, không có record bị loại không giải thích được.
- **Ngày cập nhật:** 2026-08-06

## BLOCKER-002 — Chưa tạo vector index và artifact downstream

- **Trạng thái:** OPEN
- **Phạm vi:** Clean data → embedding/index → evaluation/observability
- **Mức độ:** Blocker trước smoke query và agent test
- **Mô tả:** Clean data đã có nhưng vector index và các artifact downstream chưa được sinh ra.
- **Bằng chứng hiện tại:**
  - `data/embeddings/papers_embeddings.json` chưa tồn tại.
  - `data/chroma/` hiện chỉ có `.gitkeep`.
  - Chưa có `data/eval/test_set.json`.
  - Chưa có baseline metrics, quality report hoặc phase 1 report.
- **Ảnh hưởng:** Chưa thể chạy smoke query, exact lookup trên index, evaluation đầy đủ hoặc agent test.
- **Điều kiện đóng:**
  - Tạo thành công embedding manifest và Chroma collection.
  - Có evaluation test set.
  - Có baseline metrics, quality/freshness reports và phase 1 report.
  - Smoke query và exact lookup trả về kết quả hợp lệ.
- **Ngày cập nhật:** 2026-08-06

## WARNING-001 — `categories_joined` đang rỗng

- **Trạng thái:** OPEN
- **Phạm vi:** Clean data schema/content
- **Mức độ:** Warning, chưa phải blocker
- **Bằng chứng:** `categories_joined` rỗng ở 24/24 clean records.
- **Ảnh hưởng:** Metadata category chưa đóng góp cho retrieval hoặc evaluation.
- **Điều kiện xử lý:** Kiểm tra Crossref payload có trường `subject` hay không; nếu source thực sự không có category thì ghi nhận rõ đây là dữ liệu thiếu tự nhiên, không tự động coi là lỗi cleaning.
- **Ngày cập nhật:** 2026-08-06

## Mẫu ghi nhận vấn đề mới

### BLOCKER-XXX — <tiêu đề ngắn>

- **Trạng thái:** OPEN / IN PROGRESS / RESOLVED
- **Phạm vi:** <bước pipeline>
- **Mức độ:** Blocker / Warning
- **Mô tả:** <vấn đề>
- **Bằng chứng:** <file, metric, sample ID, log hoặc timestamp>
- **Ảnh hưởng:** <bước bị dừng>
- **Điều kiện đóng:** <tiêu chí kiểm chứng cụ thể>
- **Ngày cập nhật:** <YYYY-MM-DD>
