-- =====================================================================
-- Ý 2 - CV 835/QLT: HSSV tham gia 10/2024, còn tham gia 07/2026,
--                   tổng gián đoạn cộng dồn >= 90 ngày
-- Tuần 2 - Thứ Tư - Task 3: DDL + truy vấn. Chạy trên warehouse.db (SQLite).
-- KHÔNG đụng BC_HSSV_DUNG_THAM_GIA và TK_DBHC_HSSV_DUNG_THAM_GIA (Ý 1).
-- Quy ước tham số (giống solve.py, lưu ngày đầu tháng):
--     NGAY_GOC = '2024-10-01'     THANG_CUOI = '2026-07-01'
-- Khi chạy tháng khác, thay hai giá trị này trong các câu truy vấn bên dưới.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. DDL
-- ---------------------------------------------------------------------

-- 1.1 Bảng chi tiết: mỗi người đạt điều kiện một dòng
CREATE TABLE IF NOT EXISTS BC_HSSV_GIAN_DOAN_THAM_GIA (
    NGAY_GOC             TEXT    NOT NULL,   -- đầu tháng gốc, vd 2024-10-01
    THANG_CUOI           TEXT    NOT NULL,   -- đầu tháng hiện tại, vd 2026-07-01
    SO_SO_BHXH           TEXT    NOT NULL,
    -- định danh (lấy từ thẻ gốc)
    SO_THE_KCB           TEXT,
    HO_TEN               TEXT,
    NGAY_SINH            TEXT,
    GIOI_TINH            INTEGER,
    SO_CMND              TEXT,
    DIA_CHI              TEXT,
    -- thẻ gốc tại tháng 10/2024
    THE_GOC_ID           INTEGER,
    MA_KHOI_GOC          TEXT    NOT NULL CHECK (MA_KHOI_GOC IN ('HS', 'SV')),
    LOAI_HSSV            TEXT    NOT NULL CHECK (LOAI_HSSV IN ('HOC_SINH', 'SINH_VIEN')),
    TU_NGAY_GOC          TEXT,
    DEN_NGAY_GOC         TEXT,
    DM_BHXH_ID_GOC       INTEGER,
    MA_DVI_GOC           TEXT,
    TEN_DVI_GOC          TEXT,
    MA_TINH_GOC          TEXT,               -- tỉnh/TP dùng để thống kê
    TEN_TINH_GOC         TEXT,
    -- thẻ đại diện tại tháng 07/2026
    THE_HT_ID            INTEGER,
    MA_KHOI_HT           TEXT,
    TU_NGAY_HT           TEXT,
    DEN_NGAY_HT          TEXT,
    DM_BHXH_ID_HT        INTEGER,
    MA_DVI_HT            TEXT,
    TEN_DVI_HT           TEXT,
    MA_TINH_HT           TEXT,
    TEN_TINH_HT          TEXT,
    -- cửa sổ cá nhân và gián đoạn
    NGAY_BAT_DAU_CUA_SO  TEXT    NOT NULL,   -- ngày đầu tiên có thẻ phủ trong tháng gốc
    NGAY_KET_THUC_CUA_SO TEXT    NOT NULL,   -- ngày cuối cùng có thẻ phủ trong tháng hiện tại
    SO_KHOANG_GIAN_DOAN  INTEGER NOT NULL CHECK (SO_KHOANG_GIAN_DOAN >= 0),
    TONG_NGAY_GIAN_DOAN  INTEGER NOT NULL CHECK (TONG_NGAY_GIAN_DOAN >= 0),
    SO_THANG_QUY_DOI     REAL,               -- = TONG_NGAY_GIAN_DOAN / 30, chỉ để hiển thị
    NGUONG_NGAY          INTEGER NOT NULL DEFAULT 90,
    NGAY_XU_LY           TEXT,
    PRIMARY KEY (NGAY_GOC, THANG_CUOI, SO_SO_BHXH)
);

-- Phục vụ thống kê và xuất danh sách theo tỉnh, theo HS/SV
CREATE INDEX IF NOT EXISTS IDX_BC_GD_TINH
    ON BC_HSSV_GIAN_DOAN_THAM_GIA (NGAY_GOC, THANG_CUOI, LOAI_HSSV, MA_TINH_GOC);
-- Phục vụ truy vấn theo mức gián đoạn
CREATE INDEX IF NOT EXISTS IDX_BC_GD_NGAY
    ON BC_HSSV_GIAN_DOAN_THAM_GIA (NGAY_GOC, THANG_CUOI, TONG_NGAY_GIAN_DOAN);

-- 1.2 Bảng thống kê theo tỉnh/TP (đủ 63 tỉnh, kể cả tỉnh bằng 0)
CREATE TABLE IF NOT EXISTS TK_DBHC_HSSV_GIAN_DOAN_THAM_GIA (
    NGAY_GOC               TEXT    NOT NULL,
    THANG_CUOI             TEXT    NOT NULL,
    MA_TINH                TEXT    NOT NULL,
    TEN_TINH               TEXT,
    SL_HOC_SINH_GIAN_DOAN  INTEGER NOT NULL DEFAULT 0,
    SL_SINH_VIEN_GIAN_DOAN INTEGER NOT NULL DEFAULT 0,
    TONG_GIAN_DOAN         INTEGER NOT NULL DEFAULT 0,
    NGAY_XU_LY             TEXT,
    PRIMARY KEY (NGAY_GOC, THANG_CUOI, MA_TINH)
);


-- ---------------------------------------------------------------------
-- 2. Ghi kết quả (chạy lại nhiều lần không bị nhân đôi)
--    Trong solve_y2.py: bọc trong một transaction, bước 2.1 rồi ghi chi tiết
--    từng part, cuối cùng chạy 2.2.
-- ---------------------------------------------------------------------

-- 2.1 Xóa kết quả cũ của đúng cặp mốc
DELETE FROM BC_HSSV_GIAN_DOAN_THAM_GIA
 WHERE NGAY_GOC = '2024-10-01' AND THANG_CUOI = '2026-07-01';
DELETE FROM TK_DBHC_HSSV_GIAN_DOAN_THAM_GIA
 WHERE NGAY_GOC = '2024-10-01' AND THANG_CUOI = '2026-07-01';

-- 2.2 Sinh bảng thống kê từ bảng chi tiết (tỉnh theo cơ quan của thẻ gốc)
INSERT INTO TK_DBHC_HSSV_GIAN_DOAN_THAM_GIA
SELECT '2024-10-01', '2026-07-01', t.MA_DVI, t.TEN_DVI,
       COALESCE(SUM(CASE WHEN b.LOAI_HSSV = 'HOC_SINH'  THEN 1 ELSE 0 END), 0),
       COALESCE(SUM(CASE WHEN b.LOAI_HSSV = 'SINH_VIEN' THEN 1 ELSE 0 END), 0),
       COUNT(b.SO_SO_BHXH),
       datetime('now', 'localtime')
  FROM DM_BHXH t
  LEFT JOIN BC_HSSV_GIAN_DOAN_THAM_GIA b
         ON b.MA_TINH_GOC = t.MA_DVI
        AND b.NGAY_GOC = '2024-10-01' AND b.THANG_CUOI = '2026-07-01'
 WHERE t.MA_CHA = '00'
 GROUP BY t.MA_DVI, t.TEN_DVI;


-- ---------------------------------------------------------------------
-- 3. Truy vấn báo cáo
-- ---------------------------------------------------------------------

-- 3.1 Danh sách học sinh gián đoạn (xuất CSV)
SELECT * FROM BC_HSSV_GIAN_DOAN_THAM_GIA
 WHERE NGAY_GOC = '2024-10-01' AND THANG_CUOI = '2026-07-01' AND LOAI_HSSV = 'HOC_SINH'
 ORDER BY MA_TINH_GOC, SO_SO_BHXH;

-- 3.2 Danh sách sinh viên gián đoạn (xuất CSV)
SELECT * FROM BC_HSSV_GIAN_DOAN_THAM_GIA
 WHERE NGAY_GOC = '2024-10-01' AND THANG_CUOI = '2026-07-01' AND LOAI_HSSV = 'SINH_VIEN'
 ORDER BY MA_TINH_GOC, SO_SO_BHXH;

-- 3.3 Thống kê theo tỉnh/TP (xuất CSV)
SELECT * FROM TK_DBHC_HSSV_GIAN_DOAN_THAM_GIA
 WHERE NGAY_GOC = '2024-10-01' AND THANG_CUOI = '2026-07-01'
 ORDER BY TONG_GIAN_DOAN DESC, MA_TINH;

-- 3.4 Dòng tổng cộng toàn quốc
SELECT SUM(SL_HOC_SINH_GIAN_DOAN)  AS tong_hoc_sinh,
       SUM(SL_SINH_VIEN_GIAN_DOAN) AS tong_sinh_vien,
       SUM(TONG_GIAN_DOAN)         AS tong_chung
  FROM TK_DBHC_HSSV_GIAN_DOAN_THAM_GIA
 WHERE NGAY_GOC = '2024-10-01' AND THANG_CUOI = '2026-07-01';

-- 3.5 Phân bố theo mức gián đoạn
SELECT CASE WHEN TONG_NGAY_GIAN_DOAN < 120 THEN '090-119 ngày'
            WHEN TONG_NGAY_GIAN_DOAN < 180 THEN '120-179 ngày'
            WHEN TONG_NGAY_GIAN_DOAN < 270 THEN '180-269 ngày'
            ELSE '>= 270 ngày' END AS muc_gian_doan,
       LOAI_HSSV, COUNT(*) AS so_nguoi
  FROM BC_HSSV_GIAN_DOAN_THAM_GIA
 WHERE NGAY_GOC = '2024-10-01' AND THANG_CUOI = '2026-07-01'
 GROUP BY muc_gian_doan, LOAI_HSSV
 ORDER BY muc_gian_doan, LOAI_HSSV;

-- 3.6 Người đổi khối giữa hai mốc (HS/SV -> khối khác) và người đổi tỉnh
SELECT MA_KHOI_GOC, MA_KHOI_HT, COUNT(*) AS so_nguoi
  FROM BC_HSSV_GIAN_DOAN_THAM_GIA
 WHERE NGAY_GOC = '2024-10-01' AND THANG_CUOI = '2026-07-01'
 GROUP BY MA_KHOI_GOC, MA_KHOI_HT
 ORDER BY so_nguoi DESC;

SELECT COUNT(*) AS so_nguoi_doi_tinh
  FROM BC_HSSV_GIAN_DOAN_THAM_GIA
 WHERE NGAY_GOC = '2024-10-01' AND THANG_CUOI = '2026-07-01'
   AND MA_TINH_GOC <> MA_TINH_HT;


-- ---------------------------------------------------------------------
-- 4. Truy vấn kiểm tra (kỳ vọng ghi bên cạnh)
-- ---------------------------------------------------------------------

-- 4.1 Tổng thống kê = tổng chi tiết (kỳ vọng: chenh_lech = 0).
--     Nếu khác 0: có người có MA_TINH_GOC không thuộc DM_BHXH (mã 'XX').
SELECT (SELECT COUNT(*) FROM BC_HSSV_GIAN_DOAN_THAM_GIA
         WHERE NGAY_GOC = '2024-10-01' AND THANG_CUOI = '2026-07-01')
     - (SELECT COALESCE(SUM(TONG_GIAN_DOAN), 0) FROM TK_DBHC_HSSV_GIAN_DOAN_THAM_GIA
         WHERE NGAY_GOC = '2024-10-01' AND THANG_CUOI = '2026-07-01') AS chenh_lech;

-- 4.2 Mọi dòng đều đạt ngưỡng (kỳ vọng: 0 dòng)
SELECT SO_SO_BHXH, TONG_NGAY_GIAN_DOAN
  FROM BC_HSSV_GIAN_DOAN_THAM_GIA
 WHERE NGAY_GOC = '2024-10-01' AND THANG_CUOI = '2026-07-01'
   AND TONG_NGAY_GIAN_DOAN < NGUONG_NGAY;

-- 4.3 Mỗi người đúng một dòng (kỳ vọng: 0 dòng; khóa chính đã chặn, giữ để kiểm tra khi nạp dữ liệu)
SELECT SO_SO_BHXH, COUNT(*) AS so_dong
  FROM BC_HSSV_GIAN_DOAN_THAM_GIA
 WHERE NGAY_GOC = '2024-10-01' AND THANG_CUOI = '2026-07-01'
 GROUP BY SO_SO_BHXH HAVING COUNT(*) > 1;

-- 4.4 Cửa sổ hợp lệ: bắt đầu trong tháng gốc, kết thúc trong tháng hiện tại (kỳ vọng: 0 dòng)
SELECT SO_SO_BHXH, NGAY_BAT_DAU_CUA_SO, NGAY_KET_THUC_CUA_SO
  FROM BC_HSSV_GIAN_DOAN_THAM_GIA
 WHERE NGAY_GOC = '2024-10-01' AND THANG_CUOI = '2026-07-01'
   AND (NGAY_BAT_DAU_CUA_SO  NOT BETWEEN '2024-10-01' AND '2024-10-31'
     OR NGAY_KET_THUC_CUA_SO NOT BETWEEN '2026-07-01' AND '2026-07-31');

-- 4.5 Gián đoạn không vượt quá độ dài cửa sổ (kỳ vọng: 0 dòng)
SELECT SO_SO_BHXH
  FROM BC_HSSV_GIAN_DOAN_THAM_GIA
 WHERE NGAY_GOC = '2024-10-01' AND THANG_CUOI = '2026-07-01'
   AND TONG_NGAY_GIAN_DOAN > julianday(NGAY_KET_THUC_CUA_SO) - julianday(NGAY_BAT_DAU_CUA_SO) + 1;

-- 4.6 Bảng Ý 1 không bị ảnh hưởng: số dòng phải giữ nguyên so với trước khi chạy Ý 2
SELECT (SELECT COUNT(*) FROM BC_HSSV_DUNG_THAM_GIA)       AS y1_chi_tiet,
       (SELECT COUNT(*) FROM TK_DBHC_HSSV_DUNG_THAM_GIA)  AS y1_thong_ke;
