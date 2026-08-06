# Báo cáo cá nhân — Data, Ingestion và Corruption

## 1. Thông tin cá nhân


| Thông tin         | Nội dung                                   |
| ------------------ | ------------------------------------------- |
| Họ và tên       | Nguyễn Mai Huy                             |
| MSSV               | 2A202601712                                 |
| Khóa/Lớp         | K4                                          |
| Tên nhóm         | FIFO                                        |
| Vai trò           | Data, ingestion và corruption              |
| Repository         | `K4_Day10_Data-Pipeline-Data-Observability` |
| Ngày hoàn thành | 2026-08-06                                  |

## 2. Phạm vi sở hữu

Phần việc tập trung vào vòng đời dữ liệu từ Crossref đến clean artifact, cùng với khả năng tạo lỗi có chủ đích và phục hồi từ raw snapshot:

- Đọc Crossref payload và xác định schema `PaperRecord`.
- Crawl và lưu hai lớp raw artifact: response gốc và records đã parse.
- Chuẩn hóa dữ liệu thành DataFrame phục vụ embedding và freshness checks.
- Xác định rule null, date, duplicate, authors/categories, `text_for_embedding` và `age_days`.
- Tạo corruption có seed cố định, ghi corruption log và rebuild repaired dataset từ raw.
- Đối soát raw → clean → corrupted → repaired, ghi rõ blocker có bằng chứng.

Các file chính:

- `src/ingestion/crossref.py`
- `src/ingestion/cleaning.py`
- `src/ingestion/corruption.py`
- `src/pipelines/phase1.py`
- `src/pipelines/corruption_flow.py`
- `src/core/utils.py`
- `data/raw/`, `data/clean/`, `data/quality/`, `data/results/`, `data/reports/`

## 3. Kết quả đã thực hiện

### 3.1. Ingestion Crossref

`fetch_source_records()` gọi Crossref `/works` với query và filter từ `Settings`, sau đó ghi:

- `data/raw/crossref_response.json`: response JSON nguyên bản để recovery.
- `data/raw/crossref_records.json`: records đã parse theo `PaperRecord`.

Parser hiện xử lý title, abstract, authors, subject/categories, `issued`, `deposited`, DOI URL và PDF link. DOI được dùng làm `paper_id` trong toàn bộ pipeline. Request có retry exponential backoff cho status tạm thời `429`, `500`, `502`, `503`, `504`.

Snapshot hiện tại có bằng chứng:


| Tầng dữ liệu    | Số dòng |
| ------------------ | --------: |
| Crossref API items |        24 |
| Parsed raw records |        24 |
| Clean records      |        24 |

Không có raw record bị mất, không có DOI trùng và không có clean record phát sinh ngoài raw snapshot.

### 3.2. Cleaning contract

`build_clean_dataframe()` thực hiện:

- Chuẩn hóa whitespace cho title, summary, authors và categories.
- Parse publication date dạng `YYYY`, `YYYY-MM`, `YYYY-MM-DD`; tháng/ngày thiếu được mặc định là ngày 1.
- Dùng `published_dt` và `updated_dt` làm cột datetime nội bộ.
- Tính `age_days` từ `run_date - published_dt`.
- Tạo `authors_joined`, `categories_joined`, `summary_chars`.
- Tạo `text_for_embedding` từ title và summary.
- Loại record title dưới 3 ký tự, summary dưới 20 ký tự hoặc thiếu ngày published.
- Loại duplicate theo `paper_id`, giữ bản ghi đầu tiên.
- Sort theo publication date mới nhất trước.

Baseline artifact xác nhận:

- `row_count = 24`
- `paper_id_nulls = 0`
- `duplicate_paper_ids = 0`
- `title_nulls = 0`
- `summary_too_short = 0`
- `stale_rows = 0`
- `passed = true`

### 3.3. Corruption và recovery

`corrupt_clean_dataframe()` dùng `RANDOM_SEED = 42`, ghi đầy đủ tác động vào `data/results/corruption_log.json`, gồm:

- Drop 3 latest records.
- Blank summary ở 3 records.
- Inject noise ở 3 records.
- Truncate title ở 3 records.
- Làm stale date ở 3 records.
- Duplicate 2 records.
- Rebuild `text_for_embedding` sau corruption.

Kết quả corruption:

- Từ 24 records còn 23 rows sau drop và duplicate.
- `duplicate_paper_ids = 2`.
- `summary_too_short = 4`.
- `stale_rows = 3`.
- Quality và freshness đều fail.

Repair đọc lại `crossref_records.json`, chạy lại cleaning và tạo repaired artifacts. Kết quả repaired trở về 24 records, không duplicate, không summary ngắn và không stale row.

## 4. Evidence artifacts

- Raw response: `data/raw/crossref_response.json`
- Parsed records: `data/raw/crossref_records.json`
- Clean data: `data/clean/papers_clean.csv`, `data/clean/papers_clean.json`
- Corrupted data: `data/clean/papers_clean_corrupted.csv`, `data/clean/papers_clean_corrupted.json`
- Repaired data: `data/clean/papers_clean_repaired.csv`, `data/clean/papers_clean_repaired.json`
- Corruption log: `data/results/corruption_log.json`
- Quality reports: `data/quality/baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json`
- Freshness reports: `data/quality/freshness_report.json`, `freshness_corrupted.json`, `freshness_repaired.json`
- Pipeline reports: `data/reports/phase1_report.md`, `data/reports/corruption_report.md`

## 5. Blocker và bất thường đã ghi nhận

### Blocker 1 — Timezone mismatch khi chạy lại Phase 1

`now_utc()` trả về datetime UTC-aware tại `src/core/utils.py`, nhưng `published_dt` trong cleaning là timezone-naive. Runtime test trực tiếp cho lỗi:

```text
TypeError: Cannot subtract tz-naive and tz-aware datetime-like objects.
```

Lỗi này ảnh hưởng `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py`, vì cả hai đều gọi cleaning với `now_utc()`. Artifact baseline hiện có vẫn đọc được, nhưng cần xử lý mismatch trước khi chạy lại pipeline từ đầu.

### Blocker 2 — Categories không có trong snapshot Crossref

- API items thiếu `subject`: `24/24`.
- Parsed records có `categories` rỗng: `24/24`.
- Clean records có `categories_joined` rỗng: `24/24`.

Do đó không thể tạo câu trả lời category đáng tin cậy từ snapshot hiện tại. Đây là thiếu dữ liệu nguồn, không phải lỗi có thể sửa bằng cleaning.

### Bất thường 3 — Corpus có record tiếng Nga

Có `1/24` record được Crossref gắn `language = ru`, DOI `10.47576/2949-1894.2026.7.7.023`. Ngoài ra 16/24 record không có field language, nên không thể lọc tiếng Anh chỉ bằng metadata này.

### Bất thường 4 — Published date partial

Có 2 clean record giữ giá trị `published` dạng `YYYY-MM` (`2026-07`, `2026-05`) trong khi `published_dt` đã được parse thành ngày đầu tháng. Cần thống nhất output date trước khi dùng các quality/freshness consumer khác nhau.

## 6. Kết luận

Phần data–ingestion–corruption đã có đầy đủ raw snapshot, clean artifact, corruption log và repair artifact. Đối soát cho thấy corruption làm quality/freshness fail theo đúng thiết kế và repair phục hồi được dữ liệu từ raw.

Trạng thái bàn giao hiện tại: **artifact đã có và có bằng chứng**, nhưng **chưa nên xác nhận pipeline rerun sạch** cho đến khi xử lý timezone mismatch. Categories thiếu toàn bộ và một record tiếng Nga cần được giữ trong blocker log để người dùng downstream không hiểu nhầm là corpus tiếng Anh đầy đủ metadata.

## 7. Cách xác minh

```powershell
.\.venv\Scripts\python.exe -m compileall -q src script
python script/run_phase1.py
python script/run_corruption_flow.py
```

Các artifact sau khi chạy phải được đối chiếu lại theo chuỗi:

```text
raw response → raw records → clean → corrupted → repaired
```

**Họ và tên:** Nguyễn Quang Huy
**MSSV:** 2A202601712
**Ngày xác nhận:** 2026-08-06
