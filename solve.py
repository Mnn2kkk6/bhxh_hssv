"""
Ý 1 - CV 835/QLT: HSSV tham gia BHYT tháng 10/2024, đến nay đã dừng và chưa tham gia lại.

Logic (xử lý từng part, vì mọi thẻ của một người đều nằm trọn trong một part):
  1. Chỉ lấy thẻ hợp lệ: TRANG_THAI = 1
  2. Người "gốc"  : có thẻ MA_KHOI in (HS, SV) giao với tháng gốc
                    (TU_NGAY < đầu tháng kế tiếp  VÀ  DEN_NGAY >= đầu tháng gốc)
  3. Người "còn tham gia": có BẤT KỲ thẻ hợp lệ (mọi khối) giao với tháng kiểm tra
  4. Kết quả = (2) trừ (3)  -> đã dừng và chưa tham gia lại
  5. Mỗi người 1 dòng (thẻ gốc ưu tiên: DEN_NGAY muộn nhất, rồi TU_NGAY muộn nhất, rồi SV, rồi ID lớn)
  6. Ghi vào SQLite theo kiểu "xóa rồi ghi trong 1 transaction" => chạy lại nhiều lần kết quả không đổi.
"""
import argparse, sqlite3, time
from datetime import date, datetime
from pathlib import Path
import numpy as np
import pandas as pd
from common import list_parts, read_part, load_dm

LIGHT = ["ID", "SO_SO_BHXH", "MA_KHOI", "TU_NGAY", "DEN_NGAY", "TRANG_THAI", "DM_BHXH_ID"]
HEAVY = ["SO_THE_KCB", "HO_TEN", "NGAY_SINH", "GIOI_TINH", "SO_CMND", "DIA_CHI"]

DDL = """
CREATE TABLE IF NOT EXISTS BC_HSSV_DUNG_THAM_GIA (
    NGAY_GOC TEXT NOT NULL, NGAY_KIEM_TRA TEXT NOT NULL,
    SO_SO_BHXH TEXT NOT NULL, SO_THE_KCB TEXT, HO_TEN TEXT, NGAY_SINH TEXT, GIOI_TINH INTEGER,
    SO_CMND TEXT, DIA_CHI TEXT, THE_ID INTEGER, MA_KHOI TEXT, LOAI_HSSV TEXT,
    TU_NGAY TEXT, DEN_NGAY TEXT, DM_BHXH_ID INTEGER, MA_DVI TEXT, TEN_DVI TEXT,
    MA_TINH TEXT, TEN_TINH TEXT, NGAY_XU_LY TEXT,
    PRIMARY KEY (NGAY_GOC, NGAY_KIEM_TRA, SO_SO_BHXH)
);
CREATE INDEX IF NOT EXISTS IDX_BC_TINH ON BC_HSSV_DUNG_THAM_GIA (NGAY_GOC, NGAY_KIEM_TRA, LOAI_HSSV, MA_TINH);
CREATE TABLE IF NOT EXISTS TK_DBHC_HSSV_DUNG_THAM_GIA (
    NGAY_GOC TEXT NOT NULL, NGAY_KIEM_TRA TEXT NOT NULL, MA_TINH TEXT NOT NULL, TEN_TINH TEXT,
    SL_HOC_SINH_DUNG INTEGER, SL_SINH_VIEN_DUNG INTEGER, TONG_DUNG INTEGER, NGAY_XU_LY TEXT,
    PRIMARY KEY (NGAY_GOC, NGAY_KIEM_TRA, MA_TINH)
);
"""
DETAIL_COLS = ["NGAY_GOC", "NGAY_KIEM_TRA", "SO_SO_BHXH", "SO_THE_KCB", "HO_TEN", "NGAY_SINH", "GIOI_TINH",
               "SO_CMND", "DIA_CHI", "THE_ID", "MA_KHOI", "LOAI_HSSV", "TU_NGAY", "DEN_NGAY", "DM_BHXH_ID",
               "MA_DVI", "TEN_DVI", "MA_TINH", "TEN_TINH", "NGAY_XU_LY"]


def first_of_month(d):
    return pd.Timestamp(d.year, d.month, 1)


def first_of_next_month(d):
    return pd.Timestamp(d.year + (d.month == 12), d.month % 12 + 1, 1)


def process_part(path, goc, kt, dm_idx, ngay_xu_ly):
    g0, g1 = first_of_month(goc), first_of_next_month(goc)
    k0, k1 = first_of_month(kt), first_of_next_month(kt)

    df = read_part(path, LIGHT)
    df = df[df["TRANG_THAI"] == 1]                                   # (1) thẻ hợp lệ
    df = df.assign(_pos=df.index.to_numpy())                         # vị trí dòng để lấy cột nặng sau

    in_goc = df["MA_KHOI"].isin(["HS", "SV"]) & (df["TU_NGAY"] < g1) & (df["DEN_NGAY"] >= g0)   # (2)
    goc = df[in_goc].copy()
    if goc.empty:
        return None
    goc["_sv"] = np.where(goc["MA_KHOI"] == "SV", 0, 1)
    goc = (goc.sort_values(["SO_SO_BHXH", "DEN_NGAY", "TU_NGAY", "_sv", "ID"],
                           ascending=[True, False, False, True, False])
               .drop_duplicates("SO_SO_BHXH", keep="first"))         # (5) mỗi người một thẻ gốc

    dang_tg = df[(df["TU_NGAY"] < k1) & (df["DEN_NGAY"] >= k0)]      # (3) còn tham gia (mọi khối)
    res = goc[~goc["SO_SO_BHXH"].isin(set(dang_tg["SO_SO_BHXH"]))]   # (4)
    if res.empty:
        return None

    heavy = read_part(path, HEAVY).iloc[res["_pos"].to_numpy()]      # chỉ lấy cột nặng cho dòng kết quả
    out = pd.DataFrame({
        "NGAY_GOC": g0.strftime("%Y-%m-%d"), "NGAY_KIEM_TRA": kt.strftime("%Y-%m-%d"),
        "SO_SO_BHXH": res["SO_SO_BHXH"].to_numpy(),
        "SO_THE_KCB": heavy["SO_THE_KCB"].to_numpy(), "HO_TEN": heavy["HO_TEN"].to_numpy(),
        "NGAY_SINH": pd.to_datetime(heavy["NGAY_SINH"]).dt.strftime("%Y-%m-%d").to_numpy(),
        "GIOI_TINH": heavy["GIOI_TINH"].to_numpy(), "SO_CMND": heavy["SO_CMND"].to_numpy(),
        "DIA_CHI": heavy["DIA_CHI"].to_numpy(),
        "THE_ID": res["ID"].to_numpy(), "MA_KHOI": res["MA_KHOI"].to_numpy(),
        "LOAI_HSSV": np.where(res["MA_KHOI"] == "HS", "HOC_SINH", "SINH_VIEN"),
        "TU_NGAY": res["TU_NGAY"].dt.strftime("%Y-%m-%d").to_numpy(),
        "DEN_NGAY": res["DEN_NGAY"].dt.strftime("%Y-%m-%d").to_numpy(),
        "DM_BHXH_ID": res["DM_BHXH_ID"].to_numpy(),
    })
    dm = dm_idx.reindex(out["DM_BHXH_ID"].to_numpy())                # quy đổi cơ quan -> tỉnh/TP
    out["MA_DVI"] = dm["MA_DVI"].to_numpy()
    out["TEN_DVI"] = dm["TEN_DVI"].to_numpy()
    out["MA_TINH"] = dm["MA_TINH"].fillna("XX").to_numpy()
    out["TEN_TINH"] = dm["TEN_TINH"].fillna("Không xác định").to_numpy()
    out["NGAY_XU_LY"] = ngay_xu_ly
    return out[DETAIL_COLS]


def to_rows(df):
    return df.astype(object).where(pd.notna(df), None).values.tolist()


def export_csv(con, out_dir, goc, kt):
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"goc{goc:%Y%m}_kt{kt:%Y%m%d}"
    params = (first_of_month(goc).strftime("%Y-%m-%d"), kt.strftime("%Y-%m-%d"))
    files = []
    for loai, name in (("HOC_SINH", "ds_hoc_sinh_dung_tham_gia"), ("SINH_VIEN", "ds_sinh_vien_dung_tham_gia")):
        f = out_dir / f"{name}_{tag}.csv"
        q = ("SELECT * FROM BC_HSSV_DUNG_THAM_GIA WHERE NGAY_GOC=? AND NGAY_KIEM_TRA=? AND LOAI_HSSV=? "
             "ORDER BY MA_TINH, SO_SO_BHXH")
        pd.read_sql_query(q, con, params=params + (loai,)).to_csv(f, index=False, encoding="utf-8-sig")
        files.append(f)
    f = out_dir / f"tk_dbhc_hssv_dung_tham_gia_{tag}.csv"
    pd.read_sql_query("SELECT * FROM TK_DBHC_HSSV_DUNG_THAM_GIA WHERE NGAY_GOC=? AND NGAY_KIEM_TRA=? ORDER BY MA_TINH",
                      con, params=params).to_csv(f, index=False, encoding="utf-8-sig")
    files.append(f)
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="data")
    ap.add_argument("--db", default="warehouse.db")
    ap.add_argument("--out", default="output")
    ap.add_argument("--goc", default="2024-10", help="tháng gốc YYYY-MM")
    ap.add_argument("--kiem-tra", default="2026-08-10", help="ngày kiểm tra ('đến nay') YYYY-MM-DD")
    ap.add_argument("--no-export", action="store_true", help="không xuất CSV")
    a = ap.parse_args()

    goc = datetime.strptime(a.goc, "%Y-%m").date()
    kt = datetime.strptime(a.kiem_tra, "%Y-%m-%d").date()
    parts = list_parts(a.data)
    if not parts:
        raise SystemExit(f"Không thấy dữ liệu trong '{a.data}/ST_INTHE_DTL'. Hãy chạy gen_data.py trước.")

    dm = load_dm(a.data)
    dm_idx = dm.set_index("ID")
    ngay_xu_ly = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    k_goc, k_kt = first_of_month(goc).strftime("%Y-%m-%d"), kt.strftime("%Y-%m-%d")

    con = sqlite3.connect(a.db)
    con.isolation_level = None                      # tự quản lý transaction
    con.executescript(DDL)
    con.execute("DROP TABLE IF EXISTS DM_BHXH")
    dm[["ID", "MA_DVI", "TEN_DVI", "MA_CHA", "MA_TINH", "TEN_TINH"]].to_sql("DM_BHXH", con, index=False)

    t0, n_total = time.time(), 0
    con.execute("BEGIN")
    try:
        con.execute("DELETE FROM BC_HSSV_DUNG_THAM_GIA WHERE NGAY_GOC=? AND NGAY_KIEM_TRA=?", (k_goc, k_kt))
        con.execute("DELETE FROM TK_DBHC_HSSV_DUNG_THAM_GIA WHERE NGAY_GOC=? AND NGAY_KIEM_TRA=?", (k_goc, k_kt))
        ins = f"INSERT INTO BC_HSSV_DUNG_THAM_GIA ({','.join(DETAIL_COLS)}) VALUES ({','.join('?' * len(DETAIL_COLS))})"
        for n, p in enumerate(parts, 1):
            res = process_part(p, goc, kt, dm_idx, ngay_xu_ly)
            if res is not None:
                con.executemany(ins, to_rows(res))
                n_total += len(res)
            print(f"[{n}/{len(parts)}] {p.name}: +{0 if res is None else len(res):,} | "
                  f"tích lũy {n_total:,} | {time.time()-t0:,.0f}s", flush=True)
        con.execute("""
            INSERT INTO TK_DBHC_HSSV_DUNG_THAM_GIA
            SELECT ?, ?, t.MA_DVI, t.TEN_DVI,
                   COALESCE(SUM(CASE WHEN b.LOAI_HSSV='HOC_SINH'  THEN 1 ELSE 0 END), 0),
                   COALESCE(SUM(CASE WHEN b.LOAI_HSSV='SINH_VIEN' THEN 1 ELSE 0 END), 0),
                   COUNT(b.SO_SO_BHXH), ?
            FROM DM_BHXH t
            LEFT JOIN BC_HSSV_DUNG_THAM_GIA b
                   ON b.MA_TINH = t.MA_DVI AND b.NGAY_GOC = ? AND b.NGAY_KIEM_TRA = ?
            WHERE t.MA_CHA = '00'
            GROUP BY t.MA_DVI, t.TEN_DVI
        """, (k_goc, k_kt, ngay_xu_ly, k_goc, k_kt))
        con.execute("COMMIT")
    except BaseException:
        con.execute("ROLLBACK")                     # lỗi giữa chừng => không để lại dữ liệu dở dang.
        raise

    rows = con.execute("""SELECT MA_TINH, TEN_TINH, SL_HOC_SINH_DUNG, SL_SINH_VIEN_DUNG, TONG_DUNG
                          FROM TK_DBHC_HSSV_DUNG_THAM_GIA WHERE NGAY_GOC=? AND NGAY_KIEM_TRA=?
                          ORDER BY TONG_DUNG DESC""", (k_goc, k_kt)).fetchall()
    tot = [sum(r[i] for r in rows) for i in (2, 3, 4)]
    print(f"\n=== TỔNG HỢP (gốc {k_goc[:7]} -> kiểm tra {k_kt}) ===")
    print(f"{'Mã':<4}{'Tỉnh/TP':<28}{'Học sinh':>12}{'Sinh viên':>12}{'Tổng':>12}")
    for r in rows[:10]:
        print(f"{r[0]:<4}{r[1]:<28}{r[2]:>12,}{r[3]:>12,}{r[4]:>12,}")
    if len(rows) > 10:
        print(f"... (còn {len(rows)-10} tỉnh/TP, xem file CSV / bảng TK_DBHC_HSSV_DUNG_THAM_GIA)")
    print(f"{'':<4}{'TỔNG CỘNG':<28}{tot[0]:>12,}{tot[1]:>12,}{tot[2]:>12,}")

    if not a.no_export:
        for f in export_csv(con, Path(a.out), goc, kt):
            print("Đã xuất:", f)
    con.close()


if __name__ == "__main__":
    main()
