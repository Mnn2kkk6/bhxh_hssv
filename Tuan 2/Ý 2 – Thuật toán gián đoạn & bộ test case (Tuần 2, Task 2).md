# Ý 2 – Thuật toán gián đoạn & bộ test case

CV 835/QLT · Tuần 2 · Thứ Ba – Task 2 · Repo `bhxh_hssv`

Thuật toán chạy theo từng người trong từng part: lọc ứng viên, xác định cửa sổ cá nhân, cắt thẻ theo cửa sổ, tìm ngày trống bằng `cummax`, rồi lọc tổng ≥ 90 ngày. Bộ test gồm 20 tình huống, trong đó có hai ca biên 90/89 ngày.

## 1. Quy tắc đầu vào

| Mục | Quy tắc |
| --- | --- |
| Thẻ dùng | `TRANG_THAI = 1`, mọi khối; thẻ hủy bỏ qua hoàn toàn |
| Ngày | Bao gồm cả hai đầu mút (`TU_NGAY` và `DEN_NGAY` đều là ngày có hiệu lực) |
| Nhóm G (mốc gốc) | Có thẻ `HS`/`SV` giao tháng 10/2024: `TU_NGAY ≤ 31/10/2024` và `DEN_NGAY ≥ 01/10/2024` |
| Nhóm K (mốc hiện tại) | Có ít nhất một thẻ mọi khối giao tháng 07/2026: `TU_NGAY ≤ 31/07/2026` và `DEN_NGAY ≥ 01/07/2026` |
| Ứng viên | G ∩ K |
| Cửa sổ cá nhân | `bat_dau` = ngày sớm nhất có thẻ phủ trong tháng 10/2024; `ket_thuc` = ngày muộn nhất có thẻ phủ trong tháng 07/2026 (mọi khối) |
| Ngày trống | `TU_NGAY thẻ sau − DEN_NGAY thẻ trước − 1` (đã gộp thẻ), chỉ khi > 0 |
| Đạt | Tổng ngày trống ≥ 90 (89 không đạt) |

## 2. Pseudocode

```
INPUT : parts của ST_INTHE_DTL, DM_BHXH, goc = 2024-10, thang_cuoi = 2026-07
G0 = ngày 1 của goc          ; G1 = ngày cuối của goc
K0 = ngày 1 của thang_cuoi   ; K1 = ngày cuối của thang_cuoi

FOR EACH part:
    the = đọc cột nhẹ, giữ TRANG_THAI = 1

    # Bước 1: ứng viên
    G = người có thẻ MA_KHOI IN (HS, SV) với TU_NGAY <= G1 AND DEN_NGAY >= G0
    K = người có thẻ (mọi khối)           với TU_NGAY <= K1 AND DEN_NGAY >= K0
    ung_vien = G ∩ K
    IF rỗng: continue

    # Bước 2: thẻ gốc (giữ đúng quy tắc solve.py)
    the_goc[người] = thẻ HS/SV giao G, sắp: DEN_NGAY giảm, TU_NGAY giảm, SV trước HS, ID giảm → lấy dòng đầu

    # Bước 3: cửa sổ cá nhân
    bat_dau[người]  = MIN( MAX(TU_NGAY, G0) )  trên mọi thẻ của người đó giao G (mọi khối)
    ket_thuc[người] = MAX( MIN(DEN_NGAY, K1) ) trên mọi thẻ của người đó giao K (mọi khối)

    # Bước 4: cắt thẻ theo cửa sổ
    FOR mỗi thẻ của ứng viên:
        tu  = MAX(TU_NGAY,  bat_dau[người])
        den = MIN(DEN_NGAY, ket_thuc[người])
        bỏ thẻ nếu tu > den

    # Bước 5: tìm ngày trống bằng cummax (xử lý được thẻ lồng nhau)
    sắp theo (người, tu, den)
    den_truoc = CUMMAX(den) theo từng người, dịch xuống 1 dòng   # dòng đầu = rỗng
    ngay_trong = tu - den_truoc - 1 ; gán 0 nếu rỗng hoặc < 0
    tong[người] = SUM(ngay_trong)

    # Bước 6: lọc
    ket_qua = ứng viên có tong >= 90

    # Bước 7: thông tin báo cáo
    LOAI_HSSV = HS hoặc SV theo the_goc
    the_dai_dien_hien_tai = thẻ giao K có MIN(DEN_NGAY, K1) lớn nhất; hòa → TU_NGAY lớn nhất; hòa → ID lớn nhất
    đọc cột nặng chỉ cho ket_qua; quy đổi DM_BHXH_ID → tỉnh/TP cho thẻ gốc và thẻ đại diện
    SO_THANG_QUY_DOI = tong / 30   # chỉ hiển thị, không dùng để lọc
```

Vì cửa sổ luôn bắt đầu và kết thúc ở ngày có thẻ phủ, không có khoảng trống đầu hoặc cuối cửa sổ; chỉ có các khoảng trống ở giữa. Kiểm tra chéo: `tong = (ket_thuc − bat_dau + 1) − số ngày được phủ`.

## 3. Bộ test case

Ký hiệu: ngày dạng dd/mm/yyyy; "HS" là thẻ khối HS, "DN" là khối khác; thẻ hợp lệ nếu không ghi chú khác.

| ID | Tình huống | Thẻ | Gián đoạn | Kết quả |
| --- | --- | --- | --- | --- |
| T01 | Biên đúng 90 ngày | HS 20/10/2024–31/12/2024; HS 01/04/2025–31/07/2026 | 90 (01/01–31/03/2025: 31+28+31) | **Đạt** |
| T02 | Biên 89 ngày | HS 20/10/2024–31/12/2024; HS 31/03/2025–31/07/2026 | 89 | Không đạt |
| T03 | Thẻ nối tiếp (31/12 → 01/01) | HS 01/10/2024–31/12/2024; HS 01/01/2025–31/07/2026 | 0 | Không đạt |
| T04 | Thẻ chồng lấn | HS 01/10/2024–31/12/2024; HS 15/12/2024–31/07/2026 | 0 | Không đạt |
| T05 | Thẻ lồng trong thẻ khác (kiểm tra `cummax`) | HS 01/10/2024–31/03/2026; DN 01/01/2025–28/02/2025; DN 01/05/2026–31/07/2026 | 30 (01/04–30/04/2026); nếu chỉ so với thẻ liền trước sẽ ra 426 | Không đạt |
| T06 | Thẻ hủy phủ đúng khoảng trống | HS 01/10/2024–30/09/2025; thẻ hủy 01/10/2025–31/12/2025; DN 01/01/2026–31/07/2026 | 92 (thẻ hủy bị bỏ qua) | **Đạt** |
| T07 | Nhiều khoảng ngắn cộng dồn đúng 90 | HS 01/10/2024–31/12/2024; 31/01/2025–30/06/2025; 31/07/2025–31/12/2025; 31/01/2026–31/07/2026 | 30 + 30 + 30 = 90 | **Đạt** |
| T08 | Nhiều khoảng ngắn cộng dồn 89 | Như T07, thẻ cuối bắt đầu 30/01/2026 | 30 + 30 + 29 = 89 | Không đạt |
| T09 | Đầu cửa sổ: không tính 01–19/10/2024 | HS 20/10/2024–31/12/2024; HS 21/03/2025–31/07/2026 | 79 (nếu tính thô từ 01/10 sẽ ra 98) | Không đạt |
| T10 | Cuối cửa sổ: không tính sau ngày phủ cuối | HS 01/10/2024–10/04/2026; DN 01/07/2026–15/07/2026 | 81 (nếu tính đến 31/07 sẽ ra 97) | Không đạt |
| T11 | Chuyển HS sang đối tượng khác | HS 01/10/2024–30/06/2025; DN 01/10/2025–31/07/2026 | 92 | **Đạt**, `LOAI_HSSV = HS` |
| T12 | Không còn tham gia tháng 07/2026 | HS 01/10/2024–31/12/2024; HS 01/04/2025–30/06/2026 | 90 nhưng không thuộc K | Loại |
| T13 | Không có thẻ HS/SV tháng 10/2024 | DN 01/10/2024–31/12/2024; DN 01/06/2025–31/07/2026 | 151 nhưng không thuộc G | Loại |
| T14 | Thẻ HS ngoài tháng gốc | Một trong hai: HS 01/11/2024–31/07/2026 (bắt đầu sau); HS 01/07/2024–30/09/2024 (hết trước) | – | Loại |
| T15 | Thẻ chạm tháng 07/2026 đúng 1 ngày | HS 01/10/2024–31/12/2024; HS 01/04/2025–01/07/2026 | 90, `ket_thuc = 01/07/2026` | **Đạt** |
| T16 | Phủ trọn cửa sổ bằng một thẻ | HS 01/10/2024–31/12/2026 | 0 | Không đạt |
| T17 | Thẻ đại diện hòa ngày phủ | Giao tháng 07: P 01/01/2026–31/12/2026 (ID 200); Q 01/02/2026–31/07/2026 (ID 100) | – | Đại diện = Q (`TU_NGAY` muộn hơn) |
| T18 | Thẻ đại diện hòa tiếp | Hai thẻ cùng `TU_NGAY`, cùng phủ đến 31/07/2026, ID 100 và 200 | – | Đại diện = ID 200 |
| T19 | Tháng gốc có cả HS và SV | HS 01/09/2024–31/12/2024 (ID 10); SV 01/10/2024–31/12/2024 (ID 11) | – | Thẻ gốc = SV (cùng DEN\_NGAY, TU\_NGAY của SV muộn hơn) |
| T20 | Khoảng trống 45 ngày rồi thẻ chồng lấn | HS 01/10/2024–30/11/2024; DN 15/01/2025–10/04/2025; DN 01/04/2025–31/07/2026 | 45 (01/12/2024–14/01/2025); thẻ thứ ba chồng lên thẻ thứ hai nên không thêm | Không đạt |

## 4. Cách đối chiếu khi lập trình (thứ Năm)

- Viết hàm độc lập tính theo tập ngày: với mỗi người, dựng tập ngày được phủ trong cửa sổ rồi `tong = tổng ngày cửa sổ − số ngày được phủ`; so với kết quả `cummax`.
- Chạy toàn bộ T01–T20 như unit test trên dữ liệu dựng tay, kỳ vọng khớp bảng trên.
- Trên Fake Data nhỏ (`--persons 200000`): số người đạt từ hai cách tính phải trùng nhau; tổng thống kê tỉnh bằng tổng chi tiết; chạy hai lần số dòng không đổi.
- Kiểm tra `solve.py` Ý 1 không đổi kết quả sau khi thêm `solve_y2.py`.
