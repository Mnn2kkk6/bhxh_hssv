# Ý 2 – Phân tích nghiệp vụ & luồng dữ liệu

CV 835/QLT · Tuần 2 · Thứ Hai – Task 1 · Repo `bhxh_hssv`

## 1. Đề bài Ý 2 (viết lại ngắn gọn)

HS/SV tham gia BHYT tháng 10/2024, tháng 07/2026 **vẫn đang tham gia**, nhưng trong giai đoạn giữa hai mốc có **tổng thời gian gián đoạn ≥ 3 tháng**. Tách riêng danh sách học sinh và sinh viên.

### Ba điều kiện (phải thỏa đồng thời)

| # | Điều kiện | Cách kiểm tra |
| --- | --- | --- |
| 1 | Mốc gốc: tháng 10/2024 là HS hoặc SV | Có thẻ hợp lệ (`TRANG_THAI=1`), `MA_KHOI` ∈ {HS, SV}, `TU_NGAY` < 01/11/2024 và `DEN_NGAY` ≥ 01/10/2024 |
| 2 | Mốc hiện tại: tháng 07/2026 còn tham gia | Có thẻ hợp lệ **mọi khối** (HS, SV, DN, GD…), `TU_NGAY` < 01/08/2026 và `DEN_NGAY` ≥ 01/07/2026 |
| 3 | Giữa hai mốc: tổng ngày gián đoạn ≥ ngưỡng | Gộp mọi thẻ hợp lệ của người đó, tìm các khoảng trống, cộng dồn số ngày, so với ngưỡng **90 ngày** (đã chốt: 3 tháng = 90 ngày) |

## 2. Hiện trạng repo (đã khảo sát)

| Thành phần | Nội dung | Dùng cho Ý 2 |
| --- | --- | --- |
| `data/ST_INTHE_DTL/part_*.parquet` | Bảng thẻ; mỗi part 250.000 người, **mọi thẻ của một người nằm trọn trong một part** | Dùng nguyên, xử lý từng part |
| `data/DM_BHXH.csv` | 63 tỉnh/TP (`MA_CHA='00'`), mỗi tỉnh 6–10 cơ sở; `load_dm` thêm `MA_TINH`, `TEN_TINH` | Quy đổi cơ quan → tỉnh |
| `data/meta.json` | Số người, seed sinh dữ liệu | Ghi lại để tái lập |
| `common.py` | `list_parts`, `read_part`, `load_dm` | Import lại, không sửa |
| `solve.py` (Ý 1) | Mốc kiểm tra mặc định `--kiem-tra 2026-08-10`; ghi `BC_HSSV_DUNG_THAM_GIA`, `TK_DBHC_HSSV_DUNG_THAM_GIA` vào `warehouse.db` | Lấy khung làm mẫu, **không sửa** |
| `verify.py`, `data/SCENARIO` | Đối chiếu Ý 1 bằng cách tính độc lập | Chỉ tham khảo cách làm |

Lưu ý từ `solve.py`: thẻ gốc chọn theo thứ tự `DEN_NGAY` muộn nhất → `TU_NGAY` muộn nhất → ưu tiên SV → `ID` lớn nhất; xử lý theo `LIGHT`/`HEAVY` để tiết kiệm RAM; `process_part` lọc thẻ hợp lệ trước rồi mới đọc cột nặng. Ý 2 giữ nguyên các quy ước này.

## 3. Khác biệt Ý 1 và Ý 2

|  | Ý 1 | Ý 2 |
| --- | --- | --- |
| Mốc hiện tại | 08/2026 (mặc định `solve.py`) | **07/2026** |
| Người còn tham gia mốc hiện tại | **Loại** (chỉ lấy người đã dừng) | **Giữ** (bắt buộc còn tham gia) |
| Cần lịch sử thẻ ở giữa | Không | **Có** – toàn bộ thẻ hợp lệ giữa hai mốc |
| Phép tính | Tập A trừ tập B | Gộp khoảng thời gian → tìm khoảng trống → cộng dồn ngày |
| Tiêu chí lọc cuối | Có/không | Tổng ngày gián đoạn ≥ 90 |
| Bảng kết quả | `BC_/TK_…_DUNG_THAM_GIA` | `BC_HSSV_GIAN_DOAN_THAM_GIA`, `TK_DBHC_HSSV_GIAN_DOAN_THAM_GIA` (tên riêng) |

Bẫy cần tránh: không chạy `solve.py` với mặc định rồi coi như Ý 2; không sinh lại dữ liệu (`gen_data.py` không có `--resume` có thể xóa dữ liệu cũ).

## 4. Định nghĩa gián đoạn

- Dữ liệu ngày ở dạng timestamp 00:00, `DEN_NGAY` **bao gồm** ngày cuối (cùng quy ước `DEN_NGAY >= đầu tháng` của Ý 1).
- Chỉ xét thẻ `TRANG_THAI = 1`; thẻ hủy bỏ qua hoàn toàn.
- Thẻ nối tiếp (thẻ B bắt đầu ngay sau ngày hết hạn thẻ A) → 0 ngày gián đoạn. Thẻ chồng lấn → gộp, không tạo khoảng trống.
- Khoảng trống giữa hai khoảng đã gộp: `TU_NGAY_tiếp − DEN_NGAY_trước − 1` ngày.
- Tổng gián đoạn = cộng các khoảng trống; đạt khi **≥ 90 ngày**. Số tháng quy đổi hiển thị = ngày / 30 (chỉ để báo cáo, không dùng để lọc).

### Cửa sổ tính gián đoạn (đã chốt)

Cửa sổ cá nhân chạy từ **ngày đầu tiên có thẻ hợp lệ thực tế trong tháng 10/2024** đến **ngày cuối cùng có thẻ hợp lệ thực tế trong tháng 07/2026**; chỉ khoảng trống nằm trong cửa sổ này mới tính, không mặc định 01/10/2024 → 31/07/2026 cho mọi người.

- Gộp thẻ chồng lấn hoặc nối tiếp trước; chỉ ngày không được thẻ hợp lệ nào phủ mới là gián đoạn.
- Điều kiện tháng 07/2026 theo quy ước repo: có ít nhất một thẻ hợp lệ giao với tháng đó, không bắt buộc còn thẻ vào ngày 31/07/2026.

```latex
\text{Số ngày trống} = \max(0,\ \text{TU\_NGAY thẻ tiếp theo} - \text{DEN\_NGAY thẻ trước} - 1)
```

Tổng gián đoạn = tổng số ngày trống của mọi khoảng nằm trong cửa sổ; đạt khi ≥ 90 ngày.

| Giai đoạn | Tình trạng | Tính vào gián đoạn |
| --- | --- | --- |
| 01–19/10/2024 | Chưa có thẻ | Không (ngoài cửa sổ) |
| 20/10–31/12/2024 | Có thẻ | – |
| 01/01–31/03/2025 | Không có thẻ | Có: 31 + 28 + 31 = 90 ngày → đạt ngưỡng |
| 01/04/2025–31/07/2026 | Có thẻ | – |

Ví dụ khác: hai khoảng trống 35 và 55 ngày cộng dồn thành 90 ngày → đủ điều kiện.

## 5. Danh sách trường dữ liệu

**Cột nhẹ (đọc cho mọi người):** `ID`, `SO_SO_BHXH`, `MA_KHOI`, `TU_NGAY`, `DEN_NGAY`, `TRANG_THAI`, `DM_BHXH_ID`.

**Cột nặng (chỉ đọc cho người đạt điều kiện):** `SO_THE_KCB`, `HO_TEN`, `NGAY_SINH`, `GIOI_TINH`, `SO_CMND`, `DIA_CHI`.

**Danh mục:** `DM_BHXH` gồm `ID`, `MA_DVI`, `TEN_DVI`, `MA_CHA`, `MA_TINH`, `TEN_TINH`.

**Trường dự kiến cho bảng chi tiết Ý 2:** khóa (`NGAY_GOC`, `NGAY_KIEM_TRA`, `SO_SO_BHXH`), định danh cá nhân, `MA_KHOI`/`LOAI_HSSV` tại mốc gốc, cơ quan BHXH + tỉnh tại mốc gốc, cơ quan + tỉnh tại mốc hiện tại, `TONG_NGAY_GIAN_DOAN`, `SO_THANG_QUY_DOI`, `SO_KHOANG_GIAN_DOAN`, `NGAY_XU_LY`.

## 6. Sơ đồ luồng dữ liệu Ý 2

```
data/ST_INTHE_DTL/part_*.parquet ──┐
data/DM_BHXH.csv ──(load_dm)───────┤
                                   ▼
  Với từng part (RAM thấp, mỗi người nằm trọn 1 part):
   1. Đọc cột nhẹ, giữ TRANG_THAI = 1
   2. Tập G: có thẻ HS/SV giao tháng 10/2024  → chọn 1 thẻ gốc / người
   3. Tập K: có thẻ (mọi khối) giao tháng 07/2026
   4. Tập ứng viên = G ∩ K
   5. Với ứng viên: lấy toàn bộ thẻ hợp lệ giao cửa sổ giữa hai mốc
   6. Sort theo TU_NGAY → gộp chồng lấn/nối tiếp → tìm khoảng trống
   7. Tổng ngày gián đoạn ≥ 90 ?  → giữ
   8. Đọc cột nặng cho người được giữ; quy đổi cơ quan → tỉnh
                                   ▼
  warehouse.db (transaction, xóa rồi ghi theo NGAY_GOC + NGAY_KIEM_TRA)
   ├─ BC_HSSV_GIAN_DOAN_THAM_GIA        (chi tiết)
   └─ TK_DBHC_HSSV_GIAN_DOAN_THAM_GIA   (thống kê tỉnh/TP)
                                   ▼
  output/*.csv: ds học sinh · ds sinh viên · thống kê tỉnh/TP
```

## 7. Quyết định đã thống nhất & điểm còn mở

Mọi điểm nghiệp vụ đã chốt; có thể bắt đầu thiết kế thuật toán và lập trình.

1. **Mốc gốc:** có thẻ hợp lệ khối `HS` hoặc `SV` giao tháng 10/2024; chọn thẻ gốc theo quy tắc của `solve.py` (`DEN_NGAY` muộn nhất → `TU_NGAY` muộn nhất → ưu tiên SV → `ID` lớn nhất).
2. **Mốc hiện tại:** có ít nhất một thẻ hợp lệ, mọi khối, giao tháng 07/2026. Kiểm tra trên tất cả thẻ, không dựa vào một thẻ đại diện.
3. **Cửa sổ:** từ ngày đầu tiên có thẻ hợp lệ trong tháng 10/2024 đến ngày cuối cùng có thẻ hợp lệ trong tháng 07/2026.
4. **Cách tính:** gộp thẻ chồng lấn/nối tiếp, tìm ngày không được phủ, cộng dồn.
5. **Ngưỡng:** tổng gián đoạn ≥ 90 ngày.
6. **Phân loại:** `HS` hoặc `SV` theo thẻ gốc tháng 10/2024; tỉnh/TP theo cơ quan BHXH của thẻ gốc.
7. **Thẻ đại diện mốc hiện tại** (chỉ để ghi nhóm đối tượng và cơ quan BHXH hiện tại): thẻ hợp lệ giao tháng 07/2026 có ngày phủ muộn nhất trong tháng (cắt `DEN_NGAY` tại 31/07/2026); hòa thì `TU_NGAY` muộn nhất, rồi `ID` lớn nhất.
8. **Tham số:** `python solve_y2.py --goc 2024-10 --thang-cuoi 2026-07` (mặc định `2026-07`). Nếu giữ kiểu `solve.py` với `--kiem-tra`, chương trình dùng tháng chứa ngày được truyền vào.

## 8. Sản phẩm cuối ngày

- Tài liệu phân tích nghiệp vụ (file này) ✔
- Sơ đồ luồng dữ liệu (mục 6) ✔
- Danh sách trường dữ liệu thống nhất (mục 5) ✔
- Việc tiếp theo (thứ Ba): pseudocode gộp khoảng + bộ test case.
