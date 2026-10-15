# Tuần 1 – HSSV dừng tham gia BHYT (CV 835/QLT – Ý 1)

**Yêu cầu Ý 1:** Học sinh, sinh viên tham gia BHYT từ tháng 10/2024 nhưng đến nay đã dừng tham gia và chưa tham gia lại (tách riêng danh sách học sinh và sinh viên).

Làm 3 việc theo thứ tự: **sinh dữ liệu giả → giải Ý 1 → đối chiếu kết quả**.

---

## 1. Quy mô dữ liệu:

| Hạng mục | Con số |
|---|---|
| Số người (đối tượng) | 20 triệu (`--persons 20000000`) |
| Trong đó học sinh / sinh viên | ~3,8 triệu / ~1,2 triệu (HS 19%, SV 6%) |
| Số bản ghi thẻ `ST_INTHE_DTL` | khoảng 190 triệu (trung bình ~9,5 thẻ/người) |
| Giai đoạn | 01/2024 – 08/2026 |

.** Mỗi người có nhiều thẻ nối tiếp nhau nên 20 triệu người cho ra khoảng 200 triệu bản ghi thẻ, đúng yêu cầu đề. Tổng thực tế được in ở dòng cuối khi chạy `gen_data.py`.

---

## 2. Các file trong bộ code:

| File | Dùng để làm gì |
|---|---|
| `gen_data.py` | Sinh dữ liệu giả theo vòng đời người tham gia. |
| `solve.py` | Giải Ý 1, ghi kết quả vào `warehouse.db` và xuất CSV. |
| `verify.py` | Kiểm tra kết quả của `solve.py` bằng cách tính khác. |
| `common.py` | Hàm đọc file dùng chung (không cần chạy hay sửa). |
| `requirements.txt` | Danh sách thư viện Python cần cài: pandas, numpy, pyarrow, duckdb. |
| `README.md` | File này. |

Chỉ chạy trực tiếp 3 file: `gen_data.py`, `solve.py`, `verify.py`, theo đúng thứ tự đó.

Ngoài ra, nếu muốn truy vấn dữ liệu bằng SQL (mục 6), bạn tự tạo thêm `query.py` và các file `.sql` (nội dung có sẵn trong README).

---

## 3. Các file sinh ra sau khi chạy:

### Sau `python gen_data.py` → thư mục `data/` (dữ liệu gốc, đầu vào)

| File / thư mục | Nội dung |
|---|---|
| `data/ST_INTHE_DTL/part_*.parquet` | Bảng thẻ BHYT: số sổ BHXH, số thẻ, họ tên, ngày sinh, giới tính, CMND, địa chỉ, khối, ngày bắt đầu, ngày kết thúc, trạng thái, cơ quan BHXH. Chia thành nhiều file part (mỗi part 250.000 người, khoảng 80 part với 20 triệu người). |
| `data/DM_BHXH.csv` | Danh mục cơ quan BHXH: 63 tỉnh/TP, mỗi tỉnh 6–10 cơ sở. Cơ sở trỏ lên tỉnh qua `MA_CHA`. |
| `data/SCENARIO/part_*.parquet` | "Đáp án" do bộ sinh dữ liệu ghi sẵn: mỗi người thuộc kịch bản nào, thực tế có phải người đã dừng không. Chỉ `verify.py` dùng. |
| `data/meta.json` | Tham số đã dùng để sinh (số người, seed...), để cả nhóm biết dữ liệu được sinh thế nào. |

Dữ liệu gốc lưu **Parquet**, không phải `.db`. Parquet nén tốt và đọc nhanh, phù hợp 190 triệu dòng. Bảng `ST_INTHE_DTL` ở đây là các file Parquet, tên cột giống bảng gốc.

### Sau `python solve.py` → kết quả báo cáo

| File | Nội dung |
|---|---|
| `warehouse.db` | CSDL SQLite chứa kết quả, gồm: `BC_HSSV_DUNG_THAM_GIA` (danh sách từng HSSV đã dừng), `TK_DBHC_HSSV_DUNG_THAM_GIA` (thống kê theo tỉnh/TP) và `DM_BHXH`. File này nhỏ, không chứa 190 triệu thẻ. |
| `output/ds_hoc_sinh_dung_tham_gia_*.csv` | Danh sách **học sinh** đã dừng. |
| `output/ds_sinh_vien_dung_tham_gia_*.csv` | Danh sách **sinh viên** đã dừng. |
| `output/tk_dbhc_hssv_dung_tham_gia_*.csv` | Thống kê theo tỉnh/TP: số học sinh dừng, số sinh viên dừng, tổng. |

Ba file trong `output/` là sản phẩm nộp cho yêu cầu Ý 1. File CSV có BOM nên mở bằng Excel không lỗi tiếng Việt.

### Sau `python verify.py`
Không có file mới. Chương trình in `[ĐẠT]` hoặc `[LỖI]` cho từng kiểm tra và một dòng kết luận.

### Luồng tổng quát

```
gen_data.py → data/ (đầu vào) → solve.py → warehouse.db + output/*.csv (kết quả)
                                    ↓
                                verify.py → in [ĐẠT]/[LỖI] lên màn hình
```

---

## 4. Cách chạy bằng Terminal trong VS Code:

### Bước 0 – Mở project
1. Giải nén bộ code ra một thư mục, ví dụ `D:\hssv_bhyt`.
2. VS Code: **File → Open Folder…** → chọn thư mục đó.
3. Mở terminal: **Terminal → New Terminal** (hoặc **Ctrl + `**).

### Bước 1 – Kiểm tra Python (cần 3.9 trở lên)
```
python --version
```
Windows báo lỗi thì thử `py --version` (và dùng `py` thay cho `python` ở các lệnh sau). Chưa có Python: tải tại python.org, khi cài tick **Add Python to PATH**, rồi đóng và mở lại VS Code.

### Bước 2 – Tạo môi trường ảo và cài thư viện

**Windows (PowerShell):**
```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Nếu báo *"running scripts is disabled"*, chạy `Set-ExecutionPolicy -Scope Process Bypass` rồi kích hoạt lại.
Dùng Command Prompt thì kích hoạt bằng `.venv\Scripts\activate.bat`.

**macOS / Linux:**
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Lệnh `pip install -r requirements.txt` cài luôn cả `duckdb` (dùng cho mục 6). Nếu bạn đã cài trước đó mà chưa có duckdb, chạy lại lệnh này hoặc `pip install duckdb`.

Kích hoạt thành công khi đầu dòng lệnh có chữ `(.venv)`. Nếu VS Code hỏi chọn môi trường mới, chọn **Yes**.

### Bước 3 – Sinh dữ liệu

Chạy thử nhỏ trước (200.000 người, khoảng 1,9 triệu thẻ):
```
python gen_data.py --persons 200000
```
Chạy đủ quy mô đề bài:
```
python gen_data.py --persons 20000000 --seed 42
```
- Ước tính 10–30 phút và 10–20 GB ổ đĩa (chưa đo thực tế ở quy mô này, nên chạy thử nhỏ trước).
- Bị ngắt giữa chừng: chạy lại đúng lệnh đó kèm `--resume`.
- Máy ít RAM: thêm `--chunk 100000`.
- Cài `pyarrow` lỗi hoặc đọc/ghi Parquet lỗi: thêm `--format csv` (tốn ổ đĩa hơn nhiều).
- Cả nhóm dùng chung một bộ dữ liệu: cùng `--persons` và `--seed` thì dữ liệu giống hệt nhau từng dòng.

### Bước 4 – Giải Ý 1
```
python solve.py
```
Tùy chọn:
- `--goc 2024-10`: tháng gốc.
- `--kiem-tra 2026-08-10`: mốc "đến nay".
- `--data`, `--db`, `--out`: đổi đường dẫn dữ liệu, file CSDL, thư mục xuất.
- `--no-export`: không xuất CSV.

Kết quả: bảng thống kê theo tỉnh/TP và tổng cộng in trên terminal, cộng `warehouse.db` và thư mục `output/`.

### Bước 5 – Đối chiếu
```
python verify.py
```
Cuối cùng phải thấy `TẤT CẢ ĐẠT ✔`.

---

## 5. Cách xem dữ liệu:

Không có công cụ nào mở được cả 190 triệu dòng cùng lúc để cuộn xem. Dùng các cách sau tùy mục đích.

**Xem vài dòng đầu của một part:**
```
python -c "import pandas as pd; pd.set_option('display.width',250); pd.set_option('display.max_columns',None); print(pd.read_parquet('data/ST_INTHE_DTL/part_00000.parquet').head(20))"
```

**Xem toàn bộ lịch sử thẻ của một người** (số sổ chạy từ `1000000001` đến `1020000000`):
```
python -c "import pandas as pd; pd.set_option('display.width',250); pd.set_option('display.max_columns',None); d=pd.read_parquet('data/ST_INTHE_DTL/part_00000.parquet'); print(d[d.SO_SO_BHXH=='1000000001'].sort_values('TU_NGAY'))"
```
(Người đó phải nằm trong part được đọc. Part 00000 chứa người số 1 đến 250.000.)

**Đếm, tổng hợp trên toàn bộ dữ liệu bằng SQL:** dùng DuckDB, xem hướng dẫn và các câu truy vấn mẫu ở **mục 6**.

**Giao diện trong VS Code:**
- Extension tìm từ khóa *parquet viewer* để mở từng file part.
- Extension *SQLite Viewer* để mở `warehouse.db`.
- Extension *Rainbow CSV* để đọc CSV dễ hơn.

---

## 6. Truy vấn dữ liệu gốc bằng SQL (DuckDB)

DuckDB đọc trực tiếp các file Parquet và cho phép viết SQL, không cần cài CSDL. Cả thư mục `data/ST_INTHE_DTL/*.parquet` được coi là **một bảng duy nhất**, nên bạn không cần quan tâm dữ liệu chia thành bao nhiêu part.

> Các câu SQL trong mục này chưa được chạy thử trong quá trình làm bài. Hãy chạy thử trên dữ liệu nhỏ (`--persons 200000`) trước, và đối chiếu Q5 với kết quả của `solve.py`. Nếu lỗi, kiểm tra đường dẫn và gửi thông báo lỗi để chỉnh.

### 6.1. Cài đặt
```
pip install duckdb
```
(đã có sẵn nếu bạn chạy `pip install -r requirements.txt` với bản `requirements.txt` mới).

### 6.2. Cách chạy

**Cách 1 – Một câu lệnh trong terminal (ngắn):**
```
python -c "import duckdb; duckdb.sql(\"SELECT COUNT(*) FROM 'data/ST_INTHE_DTL/*.parquet'\").show()"
```

**Cách 2 – Viết SQL trong file rồi chạy (nên dùng cho câu dài):**

Tạo file `query.py` ở thư mục gốc project:
```python
import sys
import duckdb

con = duckdb.connect()
con.execute("SET threads TO 4")            # tăng/giảm tùy máy
con.execute("SET memory_limit = '4GB'")    # giới hạn RAM, tùy máy
sql = open(sys.argv[1], encoding="utf-8").read()
con.sql(sql).show(max_rows=50, max_width=250)
```
Tạo file `.sql` (ví dụ `q1.sql`) chứa **một câu SQL**, rồi chạy:
```
python query.py q1.sql
```
Sửa SQL trong VS Code, lưu, chạy lại lệnh là xong.

**Cách 3 – DuckDB CLI:** tải chương trình `duckdb` từ duckdb.org, mở trong terminal VS Code rồi gõ SQL tương tác.

**Lưu ý chung:**
- Chạy lệnh từ **thư mục gốc project**, vì đường dẫn `data/...` là đường dẫn tương đối.
- Truy vấn trên toàn bộ 190 triệu dòng có thể mất vài chục giây đến vài phút. Muốn thử nhanh, đọc một part: `'data/ST_INTHE_DTL/part_00000.parquet'`.
- Dữ liệu sinh bằng `--format csv` thì thay `*.parquet` bằng `*.csv`.
- Chỉ đọc thư mục `ST_INTHE_DTL`, đừng gộp chung với `SCENARIO` (khác cột).
- Các cột ngày lưu dạng timestamp (00:00:00); so sánh với `DATE '2024-10-01'` vẫn đúng.

### 6.3. Các câu truy vấn mẫu

**Q1 – Tổng số bản ghi thẻ** (`q1.sql`)
```sql
SELECT COUNT(*) AS tong_the
FROM 'data/ST_INTHE_DTL/*.parquet';
```

**Q2 – Số thẻ và số người theo khối** (`q2.sql`)
```sql
SELECT MA_KHOI,
       COUNT(*)                   AS so_the,
       COUNT(DISTINCT SO_SO_BHXH) AS so_nguoi
FROM 'data/ST_INTHE_DTL/*.parquet'
GROUP BY MA_KHOI
ORDER BY so_the DESC;
```

**Q3 – Thẻ hợp lệ và thẻ hủy** (`q3.sql`)
```sql
SELECT TRANG_THAI, COUNT(*) AS so_the
FROM 'data/ST_INTHE_DTL/*.parquet'
GROUP BY TRANG_THAI;
```

**Q4 – Lịch sử thẻ của một người** (`q4.sql`; đổi số sổ BHXH, từ `1000000001` đến `1020000000`)
```sql
SELECT ID, SO_SO_BHXH, SO_THE_KCB, MA_KHOI, TU_NGAY, DEN_NGAY, TRANG_THAI, DM_BHXH_ID
FROM 'data/ST_INTHE_DTL/*.parquet'
WHERE SO_SO_BHXH = '1000000001'
ORDER BY TU_NGAY, ID;
```

**Q5 – Số HSSV tháng 10/2024 đã dừng và chưa tham gia lại (Ý 1), tách học sinh / sinh viên** (`q5.sql`)

Cùng logic với `solve.py`: thẻ hợp lệ, một thẻ gốc mỗi người, loại người còn thẻ hợp lệ (mọi khối) giao tháng 08/2026.
```sql
WITH the_hl AS (
    SELECT ID, SO_SO_BHXH, MA_KHOI, TU_NGAY, DEN_NGAY
    FROM 'data/ST_INTHE_DTL/*.parquet'
    WHERE TRANG_THAI = 1
),
goc AS (
    SELECT *
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY SO_SO_BHXH
                   ORDER BY DEN_NGAY DESC, TU_NGAY DESC,
                            CASE WHEN MA_KHOI = 'SV' THEN 0 ELSE 1 END, ID DESC
               ) AS rn
        FROM the_hl
        WHERE MA_KHOI IN ('HS', 'SV')
          AND TU_NGAY  < DATE '2024-11-01'
          AND DEN_NGAY >= DATE '2024-10-01'
    ) AS t
    WHERE rn = 1
)
SELECT g.MA_KHOI,
       COUNT(*) AS so_nguoi_dung
FROM goc g
WHERE NOT EXISTS (
    SELECT 1
    FROM the_hl h
    WHERE h.SO_SO_BHXH = g.SO_SO_BHXH
      AND h.TU_NGAY  < DATE '2026-09-01'
      AND h.DEN_NGAY >= DATE '2026-08-01'
)
GROUP BY g.MA_KHOI
ORDER BY g.MA_KHOI;
```
Kết quả (`HS` và `SV`) phải khớp với cột "Học sinh" và "Sinh viên" của dòng TỔNG CỘNG trong `solve.py`.

**Q6 – Thống kê Ý 1 theo tỉnh/TP** (`q6.sql`)

Thêm bước quy đổi cơ quan BHXH → tỉnh qua `DM_BHXH.csv`.
```sql
WITH the_hl AS (
    SELECT ID, SO_SO_BHXH, MA_KHOI, TU_NGAY, DEN_NGAY, DM_BHXH_ID
    FROM 'data/ST_INTHE_DTL/*.parquet'
    WHERE TRANG_THAI = 1
),
goc AS (
    SELECT *
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY SO_SO_BHXH
                   ORDER BY DEN_NGAY DESC, TU_NGAY DESC,
                            CASE WHEN MA_KHOI = 'SV' THEN 0 ELSE 1 END, ID DESC
               ) AS rn
        FROM the_hl
        WHERE MA_KHOI IN ('HS', 'SV')
          AND TU_NGAY  < DATE '2024-11-01'
          AND DEN_NGAY >= DATE '2024-10-01'
    ) AS t
    WHERE rn = 1
),
dung AS (
    SELECT g.*
    FROM goc g
    WHERE NOT EXISTS (
        SELECT 1
        FROM the_hl h
        WHERE h.SO_SO_BHXH = g.SO_SO_BHXH
          AND h.TU_NGAY  < DATE '2026-09-01'
          AND h.DEN_NGAY >= DATE '2026-08-01'
    )
),
dm AS (
    SELECT ID, MA_DVI, MA_CHA,
           CASE WHEN MA_CHA = '00' THEN MA_DVI ELSE MA_CHA END AS MA_TINH
    FROM read_csv('data/DM_BHXH.csv', types = {'MA_DVI': 'VARCHAR', 'MA_CHA': 'VARCHAR'})
),
tinh AS (
    SELECT MA_DVI AS MA_TINH, TEN_DVI AS TEN_TINH
    FROM read_csv('data/DM_BHXH.csv', types = {'MA_DVI': 'VARCHAR', 'MA_CHA': 'VARCHAR'})
    WHERE MA_CHA = '00'
)
SELECT t.MA_TINH,
       t.TEN_TINH,
       SUM(CASE WHEN d.MA_KHOI = 'HS' THEN 1 ELSE 0 END) AS so_hoc_sinh_dung,
       SUM(CASE WHEN d.MA_KHOI = 'SV' THEN 1 ELSE 0 END) AS so_sinh_vien_dung,
       COUNT(*)                                          AS tong_dung
FROM dung d
JOIN dm   ON dm.ID = d.DM_BHXH_ID
JOIN tinh t ON t.MA_TINH = dm.MA_TINH
GROUP BY t.MA_TINH, t.TEN_TINH
ORDER BY tong_dung DESC;
```
Đổi hai mốc ngày (`2024-10`, `2026-08`) nếu cần kiểm tra mốc khác. Nhớ đổi **cả hai** chỗ `TU_NGAY < ...` và `DEN_NGAY >= ...` cho mỗi mốc.

**Q7 – Chỉ thử trên một part (chạy nhanh khi kiểm tra cú pháp)**
```sql
SELECT MA_KHOI, COUNT(*) AS so_the
FROM 'data/ST_INTHE_DTL/part_00000.parquet'
GROUP BY MA_KHOI;
```

### 6.4. Dùng SQL để đối chiếu với `solve.py`
Nếu nhóm bạn muốn đối chiếu số liệu giữa hai người, chạy Q5 hoặc Q6 và so với bảng tổng hợp của `solve.py` (in trên terminal hoặc file `output/tk_dbhc_hssv_dung_tham_gia_*.csv`). Hai cách làm khác nhau mà số liệu vẫn trùng là dấu hiệu logic đúng. Nếu lệch, kiểm tra các giả định ở mục 8 (cách chọn thẻ gốc, mốc "đến nay").

---

## 7. Phương pháp làm

### 7.1. Nghiệp vụ

**"Có tham gia BHYT tại tháng M"** = có ít nhất một thẻ hợp lệ (`TRANG_THAI = 1`) mà thời hạn thẻ giao với tháng M:
- `TU_NGAY < đầu tháng (M+1)` và
- `DEN_NGAY >= đầu tháng M`.

Không xét cố định một ngày, vì thẻ HSSV có thể bắt đầu và kết thúc ở ngày bất kỳ trong tháng.

**Ý 1 = tập A trừ tập B:**
- **A (mốc gốc):** có thẻ HS hoặc SV hợp lệ giao tháng 10/2024.
- **B (hiện tại):** có **bất kỳ thẻ hợp lệ nào, mọi khối**, giao tháng 08/2026 (tháng của ngày kiểm tra 10/08/2026).
- Kết quả = người thuộc A mà không thuộc B.

Vì B tính mọi khối nên:

| Tình huống | Có tính là "dừng"? |
|---|---|
| HSSV chuyển sang khối DN/GD và vẫn còn thẻ hợp lệ | Không (vẫn tham gia BHYT) |
| Dừng một thời gian rồi mua lại | Không (đã tham gia lại) |
| Chuyển trường / địa bàn, thẻ nối tiếp | Không |
| Thẻ hủy (`TRANG_THAI=0`) có hạn kéo dài | Bỏ qua thẻ hủy, vẫn là "dừng" |
| Bắt đầu sau 10/2024, hoặc hết hạn trước 10/2024 | Không thuộc tập gốc |
| Chuyển DN rồi nghỉ việc trước 08/2026 | Có |

### 7.2. Thuật toán trong `solve.py`

Xử lý **từng part** vì mọi thẻ của một người nằm trọn trong một part, nên RAM thấp và quy mô 200 triệu dòng vẫn chạy được trên laptop.

1. Đọc nhẹ các cột cần thiết, giữ thẻ có `TRANG_THAI = 1`.
2. Lọc thẻ HS/SV giao tháng 10/2024, mỗi người giữ **một thẻ gốc**.
3. Tìm tập người còn thẻ hợp lệ (mọi khối) giao tháng 08/2026.
4. Loại họ khỏi tập gốc.
5. Chỉ với số người còn lại mới đọc thêm các cột nặng (họ tên, địa chỉ...).
6. Quy đổi cơ quan BHXH về tỉnh/TP qua `DM_BHXH`.
7. Ghi vào bảng chi tiết, rồi tổng hợp theo tỉnh vào bảng thống kê.

### 7.3. Chạy lại được (idempotent)

Mỗi lần chạy: xóa kết quả cũ của đúng cặp (`NGAY_GOC`, `NGAY_KIEM_TRA`), ghi mới, trong **một transaction**. Lỗi giữa chừng thì tự rollback, không để dữ liệu dở dang và không bị nhân đôi. Bảng chi tiết có khóa chính (`NGAY_GOC`, `NGAY_KIEM_TRA`, `SO_SO_BHXH`). Thử bằng cách chạy `python solve.py` hai lần, tổng số dòng giữ nguyên.

### 7.4. Cách sinh dữ liệu theo vòng đời

- Mỗi người có 1–2 giai đoạn; mỗi giai đoạn là chuỗi thẻ nối tiếp, chu kỳ 1/3/6/12 tháng.
- Độ tuổi đúng khối: Học sinh 6–18, Sinh viên 18–25, Trẻ em dưới 6.
- Thẻ HSSV tập trung bắt đầu tháng 1 hoặc tháng 10; kết thúc nhiều vào mùa hè (tháng 6–9).
- Các kịch bản của HSSV: tham gia liên tục · dừng hẳn · chuyển DN/GD (tiếp tục hoặc rồi dừng) · chuyển trường/địa bàn (tiếp tục hoặc rồi dừng) · gián đoạn rồi quay lại · bắt đầu sau 10/2024 · hết hạn trước 10/2024 · chỉ có thẻ hủy · dừng kèm thẻ hủy "kéo dài" · học sinh lên sinh viên.
- Trẻ em dưới 6 tuổi lên Học sinh từ năm 2025; khoảng 3% thẻ có bản ghi cấp đổi/hủy.
- Số ngẫu nhiên tính theo (mã người, seed) nên cùng tham số thì ra cùng dữ liệu, bất kể chia part thế nào.

### 7.5. Cách đối chiếu trong `verify.py`

| Kiểm tra | Ý nghĩa |
|---|---|
| (A) Cách tính độc lập | Quy ngày về chỉ số tháng rồi dùng groupby/any, khác hẳn cách lọc ngày và loại trừ của `solve.py`. Hai tập người phải trùng nhau. |
| (A) Phân loại HS/SV | Khớp với cách tính độc lập (với người không mơ hồ). |
| (B) Đáp án kịch bản | Tập người dừng phải bằng đáp án ghi sẵn trong `SCENARIO`. |
| (C) Tự nhất quán | Mỗi người đúng một dòng; tổng thống kê bằng tổng chi tiết. |
| Thông tin thêm | Nếu quên lọc `TRANG_THAI=1` thì kết quả lệch bao nhiêu. |

Trên dữ liệu thử 100.000 người, tất cả kiểm tra đều đạt.

### 7.6. Công nghệ

Python + pandas + numpy, dữ liệu gốc Parquet chia part, kết quả SQLite. Logic (lọc → giao tháng → loại trừ → một dòng mỗi người → gộp tỉnh) chuyển sang Spark/SQL (Oracle, Hive...) rất trực tiếp khi lên hệ thống thật.

---

## 8. Các giả định cần thống nhất với bạn cùng nhóm

1. **Mỗi người một dòng.** Nếu tháng 10/2024 có cả thẻ HS và SV, lấy thẻ có `DEN_NGAY` muộn nhất; hòa thì `TU_NGAY` muộn nhất; hòa nữa thì ưu tiên SV; cuối cùng `ID` lớn nhất.
2. **Tỉnh/TP theo cơ quan quản lý thẻ gốc** (tháng 10/2024), quy đổi qua `DM_BHXH`. Tỉnh có `MA_CHA = '00'`; cơ sở có `MA_CHA` là mã tỉnh.
3. **"Đến nay" xét theo tháng** của ngày kiểm tra (08/2026), cùng quy tắc giao thời gian như tháng gốc.
4. **Người đã chuyển khối khác nhưng còn thẻ hợp lệ không tính là dừng** (vì vẫn tham gia BHYT).

Nếu nhóm hiểu khác ở điểm nào, đổi điều kiện tương ứng trong `solve.py` rồi so lại số liệu giữa các bạn.

---

## 9. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `python` không nhận | Thử `py`; hoặc cài lại Python và tick Add to PATH. |
| Không kích hoạt được `.venv` trên PowerShell | `Set-ExecutionPolicy -Scope Process Bypass` rồi kích hoạt lại. |
| Cài `pyarrow` lỗi hoặc lỗi đọc/ghi Parquet | Chạy `gen_data.py` với `--format csv`. |
| Hết RAM | Giảm `--chunk`, ví dụ `--chunk 100000`. |
| Bị ngắt khi sinh dữ liệu | Chạy lại lệnh cũ kèm `--resume`. |
| `solve.py` báo không thấy dữ liệu | Chạy `gen_data.py` trước, hoặc chỉ đúng thư mục bằng `--data`. |
| `ModuleNotFoundError: No module named 'duckdb'` | Chưa kích hoạt `.venv` hoặc chưa cài: `pip install duckdb`. |
| DuckDB báo không thấy file | Đang chạy ngoài thư mục gốc project hoặc sai đường dẫn `data/ST_INTHE_DTL/*.parquet`. |
| DuckDB báo hết bộ nhớ | Giảm `memory_limit` / `threads` trong `query.py`, hoặc thử trên một part. |
| `verify.py` báo `[LỖI]` | Chạy lại `solve.py`, kiểm tra hai lệnh dùng cùng `--goc`, `--kiem-tra` và cùng thư mục dữ liệu. |
