import csv, os, sqlite3

DB = "warehouse.db"
OUT = "output_y2"
GOC, CUOI = "2024-10-01", "2026-07-01"          # đổi khi chạy mốc khác
TAG = f"goc{GOC[:4]}{GOC[5:7]}_cuoi{CUOI[:4]}{CUOI[5:7]}"

BC = "BC_HSSV_GIAN_DOAN_THAM_GIA"
TK = "TK_DBHC_HSSV_GIAN_DOAN_THAM_GIA"
WHERE = "WHERE NGAY_GOC = ? AND THANG_CUOI = ?"

JOBS = [
    (f"ds_hoc_sinh_gian_doan_tham_gia_{TAG}.csv",
     f"SELECT * FROM {BC} {WHERE} AND LOAI_HSSV = 'HOC_SINH' ORDER BY MA_TINH_GOC, SO_SO_BHXH"),
    (f"ds_sinh_vien_gian_doan_tham_gia_{TAG}.csv",
     f"SELECT * FROM {BC} {WHERE} AND LOAI_HSSV = 'SINH_VIEN' ORDER BY MA_TINH_GOC, SO_SO_BHXH"),
    (f"tk_dbhc_hssv_gian_doan_tham_gia_{TAG}.csv",
     f"SELECT * FROM {TK} {WHERE} ORDER BY TONG_GIAN_DOAN DESC, MA_TINH"),
]

os.makedirs(OUT, exist_ok=True)
con = sqlite3.connect(DB)
for name, sql in JOBS:
    cur = con.execute(sql, (GOC, CUOI))
    rows = cur.fetchall()
    path = os.path.join(OUT, name)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:   # mở bằng Excel không lỗi font
        w = csv.writer(f)
        w.writerow([d[0] for d in cur.description])
        w.writerows(rows)
    print(f"{path}: {len(rows)} dòng")
con.close()