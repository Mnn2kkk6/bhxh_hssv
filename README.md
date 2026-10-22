# BHXH HSSV — Xử lý bài toán BHYT theo Công văn 835/QLT

Repository triển khai hai bài toán xử lý dữ liệu học sinh, sinh viên (HSSV) tham gia bảo hiểm y tế (BHYT), sử dụng bộ dữ liệu giả lập quy mô lớn để kiểm thử thuật toán và tổng hợp báo cáo theo tỉnh/thành phố.

**Phạm vi:** Ý 1 — HSSV đã dừng tham gia; Ý 2 — HSSV vẫn tham gia nhưng có thời gian gián đoạn cộng dồn từ 90 ngày trở lên.

> Dữ liệu trong dự án là **dữ liệu giả lập**, phục vụ phát triển và kiểm thử thuật toán; không phải dữ liệu nghiệp vụ thật.

---

## Mục lục

- [Bài toán và quy tắc nghiệp vụ](#bài-toán-và-quy-tắc-nghiệp-vụ)
- [Cách tiếp cận](#cách-tiếp-cận)
- [Cấu trúc repository](#cấu-trúc-repository)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Cài đặt](#cài-đặt)
- [Chạy chương trình](#chạy-chương-trình)
- [Kiểm thử](#kiểm-thử)
- [Định dạng kết quả](#định-dạng-kết-quả)
- [Truy vấn dữ liệu](#truy-vấn-dữ-liệu)
- [Lưu ý khi làm việc với dữ liệu lớn](#lưu-ý-khi-làm-việc-với-dữ-liệu-lớn)

---

## Bài toán và quy tắc nghiệp vụ

### Ý 1 — HSSV dừng tham gia BHYT

**Mục tiêu:** Lập riêng danh sách học sinh và sinh viên có tham gia BHYT trong tháng 10/2024 nhưng đã dừng tham gia và chưa tham gia lại tại tháng kiểm tra.

Một người thuộc kết quả khi đồng thời thỏa mãn:

1. Có ít nhất một thẻ hợp lệ (`TRANG_THAI = 1`) thuộc khối `HS` hoặc `SV`, giao với tháng 10/2024.
2. Không có thẻ hợp lệ thuộc bất kỳ khối nào giao với tháng kiểm tra.
3. Mỗi người chỉ xuất hiện một lần trong danh sách kết quả.

Mặc định, tháng kiểm tra là tháng 08/2026, với tham số `--kiem-tra 2026-08-10`. Tham số này là ngày dùng để xác định tháng kiểm tra; phép kiểm tra tham gia được thực hiện trên toàn bộ tháng đó.

### Ý 2 — HSSV vẫn tham gia nhưng gián đoạn từ 90 ngày

**Mục tiêu:** Tìm HSSV tham gia trong tháng 10/2024, vẫn có thẻ hợp lệ giao tháng 07/2026, nhưng tổng thời gian không được thẻ hợp lệ nào bao phủ trong khoảng giữa hai mốc đạt ít nhất 90 ngày.

Các quy tắc chính:

- **Thẻ hợp lệ:** Chỉ xét thẻ có `TRANG_THAI = 1`; thẻ hủy bị bỏ qua.
- **Mốc gốc:** Có thẻ khối `HS` hoặc `SV` giao tháng 10/2024.
- **Mốc hiện tại:** Có ít nhất một thẻ hợp lệ thuộc bất kỳ khối nào giao tháng 07/2026.
- **Cửa sổ cá nhân:** Từ ngày đầu tiên có thẻ hợp lệ bao phủ trong tháng gốc đến ngày cuối cùng có thẻ hợp lệ bao phủ trong tháng hiện tại. Không mặc định mọi người đều bắt đầu ngày 01/10/2024 và kết thúc ngày 31/07/2026.
- **Ngày có hiệu lực:** Bao gồm cả `TU_NGAY` và `DEN_NGAY`.
- **Khoảng gián đoạn:** Sau khi gộp các thẻ chồng lấn hoặc nối tiếp, số ngày trống giữa hai khoảng là:

  `Số ngày trống = TU_NGAY tiếp theo - DEN_NGAY trước đó - 1`

- **Ngưỡng:** Tổng số ngày trống cộng dồn phải **≥ 90 ngày**. Đúng 90 ngày đạt điều kiện; 89 ngày không đạt.
- **Phân loại:** Phân loại học sinh/sinh viên theo thẻ gốc ở tháng 10/2024. Tỉnh/TP thống kê theo cơ quan BHXH của thẻ gốc; thông tin cơ quan BHXH của thẻ đại diện tháng 07/2026 cũng được lưu để đối chiếu.

Ví dụ biên: khoảng trống từ 01/01/2025 đến 31/03/2025 gồm 90 ngày (31 + 28 + 31), nên đạt ngưỡng.

## Cách tiếp cận

### Luồng xử lý tổng thể

```text
Dữ liệu Parquet + danh mục cơ quan BHXH
                  |
                  v
       Đọc và xử lý từng part
                  |
        +---------+---------+
        |                   |
        v                   v
   solve.py             solve_y2.py
      Ý 1                   Ý 2
        |                   |
        +---------+---------+
                  v
          warehouse.db
                  |
         +--------+--------+
         |                 |
         v                 v
    Báo cáo CSV       Thống kê tỉnh/TP
         |
         v
       verify.py / test_y2.py
```

### Ý 1

`solve.py` lọc các thẻ hợp lệ, xác định người thuộc nhóm HSSV ở tháng gốc, rồi loại người còn thẻ hợp lệ giao tháng kiểm tra. Chương trình chọn một thẻ gốc đại diện cho mỗi người và lưu kết quả chi tiết, thống kê vào SQLite.

`verify.py` đối chiếu kết quả bằng cách tính độc lập theo tháng, so sánh với kịch bản đáp án do bộ sinh dữ liệu tạo ra, đồng thời kiểm tra tính duy nhất và sự khớp nhau giữa bảng chi tiết với bảng thống kê.

### Ý 2

`solve_y2.py` xử lý theo từng part, không cần nạp toàn bộ dữ liệu vào RAM cùng lúc:

1. Lọc thẻ hợp lệ và xác định người có thẻ HS/SV giao tháng 10/2024.
2. Xác định người có thẻ hợp lệ bất kỳ giao tháng 07/2026; lấy giao của hai tập làm tập ứng viên.
3. Tính cửa sổ riêng của mỗi người từ ngày có thẻ phủ đầu tiên ở tháng gốc đến ngày có thẻ phủ cuối cùng ở tháng hiện tại.
4. Cắt các khoảng thẻ theo cửa sổ cá nhân; sắp xếp theo ngày và dùng `cummax` để gộp đúng cả những khoảng lồng nhau.
5. Cộng dồn số ngày không được phủ và giữ người đạt ngưỡng.
6. Chọn thẻ gốc và thẻ đại diện tháng hiện tại theo quy tắc xác định; chỉ đọc các cột thông tin cá nhân cần thiết cho những người đạt điều kiện.
7. Ghi dữ liệu trong transaction SQLite. Nếu xử lý lỗi, transaction được rollback; chạy lại cùng cặp mốc sẽ thay thế kết quả cũ của đúng cặp mốc đó.

Hai bài toán dùng **các bảng kết quả riêng**, vì vậy chạy Ý 2 không ghi đè bảng chi tiết hoặc thống kê của Ý 1.

---

## Cấu trúc repository

| File / thư mục | Chức năng |
|---|---|
| `gen_data.py` | Sinh dữ liệu BHYT giả lập theo vòng đời người tham gia. |
| `data/ST_INTHE_DTL/part_*.parquet` | Các phần dữ liệu thẻ BHYT đầu vào. |
| `data/DM_BHXH.csv` | Danh mục cơ quan BHXH dùng để quy đổi cơ quan sang tỉnh/TP. |
| `data/SCENARIO/part_*.parquet` | Kịch bản đáp án do bộ sinh dữ liệu tạo, dùng để kiểm chứng Ý 1. |
| `data/meta.json` | Lưu tham số sinh dữ liệu, gồm số người, seed và định dạng. |
| `common.py` | Hàm đọc từng part và nạp danh mục dùng chung. |
| `solve.py` | Thuật toán Ý 1; ghi bảng kết quả và xuất CSV. |
| `verify.py` | Đối chiếu độc lập kết quả Ý 1. |
| `solve_y2.py` | Thuật toán Ý 2; tự tạo bảng, xử lý dữ liệu và xuất CSV. |
| `test_y2.py` | Bộ test thuật toán Ý 2 với các trường hợp dựng sẵn và dữ liệu ngẫu nhiên. |
| `export_y2.py` | Tiện ích xuất lại các CSV Ý 2 từ `warehouse.db` theo các mốc cấu hình trong file. |
| `y2_ddl_queries.sql` | DDL và các truy vấn tham khảo cho bảng kết quả Ý 2. |
| `run_sql.py` | Tiện ích chạy tập lệnh SQL trên SQLite. |
| `requirements.txt` | Danh sách thư viện Python. |
| `Tuan 2/` | Tài liệu phân tích nghiệp vụ, luồng dữ liệu, thuật toán và test case của Ý 2. |
| `output/` | CSV kết quả Ý 1. |
| `output_y2/` | CSV kết quả Ý 2. |
| `warehouse.db` | Cơ sở dữ liệu SQLite được tạo khi chạy chương trình. |

### Dữ liệu hiện có

Theo `data/meta.json`, bộ dữ liệu được cấu hình với:

| Tham số | Giá trị |
|---|---|
| Số người | 20.000.000 |
| Seed | `42` |
| Kích thước mỗi chunk khi sinh | 250.000 người |
| Định dạng dữ liệu thẻ | Parquet |
| Thời gian mô phỏng | 01/2024–08/2026 |

Số bản ghi thẻ thực tế có thể thay đổi theo kết quả sinh dữ liệu. Bộ dữ liệu và các CSV kết quả có dung lượng lớn; hãy kiểm tra dung lượng ổ đĩa trước khi tải hoặc tạo lại dữ liệu.

---

## Công nghệ sử dụng

- **Python** — triển khai thuật toán và luồng xử lý.
- **Pandas / NumPy** — lọc, sắp xếp, tổng hợp dữ liệu theo từng part.
- **Parquet / PyArrow** — lưu trữ và đọc dữ liệu lớn theo từng phần.
- **SQLite** — lưu kết quả chi tiết, bảng thống kê và hỗ trợ chạy lại theo từng cặp mốc.
- **DuckDB** — truy vấn phân tích dữ liệu Parquet bằng SQL.
- **CSV UTF-8 with BOM** — xuất danh sách có thể mở bằng Excel mà hạn chế lỗi font tiếng Việt.

---

## Cài đặt

Yêu cầu Python 3.9 trở lên. Các lệnh dưới đây chạy từ thư mục gốc của repository.

### 1. Tạo môi trường ảo

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Nếu PowerShell chặn kích hoạt môi trường, có thể cho phép trong phiên terminal hiện tại rồi kích hoạt lại:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## Chạy chương trình

### Sử dụng dữ liệu đã có trong repository

Nếu thư mục `data/` đã chứa các part Parquet và `DM_BHXH.csv`, **không cần chạy lại `gen_data.py`**.

#### Bước 1 — Giải Ý 1

```bash
python solve.py --goc 2024-10 --kiem-tra 2026-08-10
```

Chương trình mặc định đọc `data/`, lưu vào `warehouse.db` và xuất kết quả trong `output/`.

#### Bước 2 — Kiểm chứng Ý 1

```bash
python verify.py --goc 2024-10 --kiem-tra 2026-08-10
```

Kiểm tra kết luận cuối cùng trên terminal. Nếu có mục `[LỖI]`, hãy xem chi tiết đối chiếu trước khi sử dụng kết quả.

#### Bước 3 — Giải Ý 2

```bash
python solve_y2.py --goc 2024-10 --thang-cuoi 2026-07 --nguong 90
```

Chương trình mặc định đọc `data/`, cập nhật các bảng Ý 2 trong `warehouse.db` và xuất ba CSV vào `output_y2/`. Các bảng Ý 1 được giữ riêng.

#### Xem tham số hỗ trợ

```bash
python solve.py --help
python verify.py --help
python solve_y2.py --help
python gen_data.py --help
```

### Sinh bộ dữ liệu nhỏ để thử nghiệm

Chỉ dùng bước này khi muốn tạo dữ liệu thử riêng. Đặt dữ liệu vào `data_small/` để tránh ghi đè bộ dữ liệu hiện có trong `data/`.

```bash
python gen_data.py --persons 200000 --seed 42 --chunk 50000 --out data_small
```

Sau khi sinh dữ liệu, chạy Ý 1 và Ý 2 trên cùng cơ sở dữ liệu thử nghiệm:

```bash
python solve.py --data data_small --db warehouse_small.db --out output_y1_small
python verify.py --data data_small --db warehouse_small.db
python solve_y2.py --data data_small --db warehouse_small.db --out output_y2_small
```

Khi cần tái lập cùng một bộ dữ liệu, dùng cùng giá trị `--persons` và `--seed`. Không chạy lệnh sinh dữ liệu trên thư mục đầu vào đang sử dụng nếu chưa sao lưu.

### Tham số thường dùng

| Chương trình | Tham số | Ý nghĩa |
|---|---|---|
| `gen_data.py` | `--persons` | Số người cần sinh. |
| `gen_data.py` | `--seed` | Seed để tái lập dữ liệu. |
| `gen_data.py` | `--chunk` | Số người xử lý mỗi chunk khi sinh. |
| `gen_data.py` | `--out` | Thư mục dữ liệu đầu ra. |
| `solve.py` / `verify.py` | `--data` | Thư mục chứa dữ liệu đầu vào. |
| `solve.py` / `verify.py` | `--db` | Đường dẫn cơ sở dữ liệu SQLite. |
| `solve.py` | `--goc` | Tháng gốc, định dạng `YYYY-MM`. |
| `solve.py` / `verify.py` | `--kiem-tra` | Ngày dùng để xác định tháng kiểm tra, định dạng `YYYY-MM-DD`. |
| `solve_y2.py` | `--goc` | Tháng gốc, mặc định `2024-10`. |
| `solve_y2.py` | `--thang-cuoi` | Tháng hiện tại, mặc định `2026-07`. |
| `solve_y2.py` | `--nguong` | Ngưỡng gián đoạn tính theo ngày, mặc định `90`. |
| Các script xử lý | `--out` | Thư mục xuất CSV, nếu script có hỗ trợ. |

---

## Kiểm thử

### Test Ý 2

`test_y2.py` có 20 tình huống kiểm thử dựng sẵn, bao gồm:

- Khoảng trống đúng 90 ngày và 89 ngày.
- Thẻ nối tiếp, chồng lấn và lồng nhau.
- Thẻ bị hủy.
- Nhiều khoảng trống ngắn được cộng dồn.
- Cửa sổ cá nhân không bắt đầu đúng ngày 01/10 hoặc không kết thúc ngày 31/07.
- Không đủ điều kiện ở mốc gốc hoặc mốc hiện tại.
- Quy tắc chọn thẻ gốc và thẻ đại diện tháng hiện tại.

Bộ test còn so sánh thuật toán gộp khoảng với cách tính độc lập bằng tập ngày trên dữ liệu ngẫu nhiên.

Chạy:

```bash
python test_y2.py
```

### Các đối chiếu nên thực hiện sau khi xử lý

- Mỗi người chỉ có một dòng trong bảng chi tiết theo cặp mốc.
- Tổng số người trong bảng thống kê bằng tổng số dòng trong bảng chi tiết.
- Mọi bản ghi Ý 2 đều có `TONG_NGAY_GIAN_DOAN >= NGUONG_NGAY`.
- Kết quả Ý 1 vượt qua các bước kiểm tra của `verify.py`.
- Khi chạy lại cùng tham số, số dòng kết quả không bị nhân đôi.

---

## Định dạng kết quả

### Ý 1

Trong `warehouse.db`:

- `BC_HSSV_DUNG_THAM_GIA` — danh sách chi tiết HSSV đã dừng tham gia.
- `TK_DBHC_HSSV_DUNG_THAM_GIA` — thống kê học sinh, sinh viên và tổng số theo tỉnh/TP.

Các CSV được xuất vào `output/`, gồm danh sách học sinh, danh sách sinh viên và bảng thống kê tỉnh/TP.

### Ý 2

Trong `warehouse.db`:

- `BC_HSSV_GIAN_DOAN_THAM_GIA` — danh sách chi tiết người đạt điều kiện.
- `TK_DBHC_HSSV_GIAN_DOAN_THAM_GIA` — thống kê theo tỉnh/TP.

Các trường nổi bật trong bảng chi tiết gồm:

| Trường | Ý nghĩa |
|---|---|
| `SO_SO_BHXH` | Mã định danh người tham gia trong bộ dữ liệu. |
| `LOAI_HSSV` | Phân loại `HOC_SINH` hoặc `SINH_VIEN` theo thẻ gốc. |
| `MA_KHOI_GOC` | Khối đối tượng của thẻ gốc. |
| `MA_KHOI_HT` | Khối đối tượng của thẻ đại diện ở tháng hiện tại. |
| `MA_TINH_GOC`, `TEN_TINH_GOC` | Tỉnh/TP theo cơ quan của thẻ gốc. |
| `MA_TINH_HT`, `TEN_TINH_HT` | Tỉnh/TP theo cơ quan của thẻ đại diện hiện tại. |
| `NGAY_BAT_DAU_CUA_SO` | Ngày đầu tiên có thẻ phủ trong tháng gốc. |
| `NGAY_KET_THUC_CUA_SO` | Ngày cuối cùng có thẻ phủ trong tháng hiện tại. |
| `SO_KHOANG_GIAN_DOAN` | Số khoảng gián đoạn. |
| `TONG_NGAY_GIAN_DOAN` | Tổng số ngày gián đoạn cộng dồn. |
| `SO_THANG_QUY_DOI` | Số tháng quy đổi để hiển thị, tính bằng tổng ngày chia 30; không dùng làm điều kiện lọc. |
| `NGUONG_NGAY` | Ngưỡng dùng để xác định kết quả. |

Các CSV Ý 2 có tên theo mốc xử lý, ví dụ:

- `output_y2/ds_hoc_sinh_gian_doan_tham_gia_goc202410_cuoi202607.csv`
- `output_y2/ds_sinh_vien_gian_doan_tham_gia_goc202410_cuoi202607.csv`
- `output_y2/tk_dbhc_hssv_gian_doan_tham_gia_goc202410_cuoi202607.csv`

Tất cả CSV được ghi với mã hóa `utf-8-sig` để hỗ trợ mở bằng Excel.

---

## Truy vấn dữ liệu

Có thể dùng DuckDB để phân tích trực tiếp dữ liệu Parquet, không cần nhập tất cả dữ liệu vào SQLite.

Ví dụ đếm số bản ghi thẻ:

```bash
python -c "import duckdb; duckdb.sql(\"SELECT COUNT(*) FROM 'data/ST_INTHE_DTL/*.parquet'\").show()"
```

Để xem lịch sử thẻ của một người, có thể dùng Pandas hoặc truy vấn DuckDB với điều kiện `SO_SO_BHXH`. Không gộp thư mục `SCENARIO` vào truy vấn bảng thẻ vì đây là dữ liệu khác cấu trúc.

File `y2_ddl_queries.sql` chứa DDL và các truy vấn báo cáo/thẩm tra tham khảo cho Ý 2. Trong quy trình thông thường, `solve_y2.py` đã tự tạo bảng và chỉ mục cần thiết nên không cần chạy DDL thủ công.

---

## Lưu ý khi làm việc với dữ liệu lớn

- Bắt đầu bằng bộ dữ liệu nhỏ để xác nhận môi trường và quy trình trước khi chạy toàn bộ dữ liệu.
- Mỗi part được xử lý riêng; tránh tự đọc hoặc ghép toàn bộ hàng triệu bản ghi vào một DataFrame nếu máy không đủ RAM.
- Chỉ đọc các cột cần thiết khi xử lý. Chương trình chỉ nạp các cột thông tin cá nhân bổ sung cho những người được giữ lại.
- Không sinh lại dữ liệu vào thư mục `data/` đang sử dụng nếu chưa có bản sao lưu.
- `warehouse.db` lưu kết quả báo cáo, không thay thế bộ dữ liệu thẻ Parquet đầu vào.
- Kết quả phụ thuộc vào bộ dữ liệu, mốc tháng và ngưỡng được truyền vào; hãy lưu lại tham số khi cần tái lập báo cáo.

---

## Tài liệu liên quan

- [Phân tích nghiệp vụ và luồng dữ liệu — Ý 2](Tuan%202/Ý%202%20–%20Phân%20tích%20nghiệp%20vụ%20%26%20luồng%20dữ%20liệu%20(Tuần%202,%20Task%201).md)
- [Thuật toán gián đoạn và bộ test case — Ý 2](Tuan%202/Ý%202%20–%20Thuật%20toán%20gián%20đoạn%20%26%20bộ%20test%20case%20(Tuần%202,%20Task%202).md)
