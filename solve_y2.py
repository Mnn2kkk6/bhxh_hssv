"""
Ý 2 - CV 835/QLT: HSSV tham gia BHYT tháng 10/2024, tháng 07/2026 vẫn tham gia,
nhưng tổng thời gian gián đoạn cộng dồn >= 90 ngày (tách riêng học sinh / sinh viên).

Quy tắc nghiệp vụ (đã thống nhất):
1. Chỉ dùng thẻ hợp lệ: TRANG_THAI = 1 (thẻ hủy bỏ qua hoàn toàn).
2. Nhóm G: có thẻ HS/SV giao tháng gốc (10/2024).
3. Nhóm K: có ít nhất một thẻ (mọi khối) giao tháng cuối (07/2026).
4. Ứng viên = G ∩ K.
5. Cửa sổ cá nhân: từ ngày đầu tiên có thẻ phủ trong tháng gốc đến ngày cuối cùng có thẻ phủ
   trong tháng cuối (thẻ mọi khối). Chỉ khoảng trống nằm trong cửa sổ mới tính.
6. Gộp thẻ chồng lấn/nối tiếp (cummax của DEN_NGAY), ngày trống = TU_NGAY sau - DEN_NGAY trước - 1.
7. Đạt khi tổng ngày trống >= 90. Ngày tính bao gồm cả hai đầu mút.
8. Thẻ gốc: quy tắc của solve.py (DEN_NGAY muộn nhất, TU_NGAY muộn nhất, ưu tiên SV, ID lớn nhất).
   Thẻ đại diện tháng cuối: ngày phủ trong tháng muộn nhất (cắt tại ngày cuối tháng),
   rồi TU_NGAY muộn nhất, rồi ID lớn nhất.
9. Tỉnh/TP theo cơ quan BHXH của thẻ gốc; lưu thêm cơ quan/tỉnh của thẻ đại diện hiện tại.
10. Ghi vào SQLite kiểu "xóa rồi ghi trong 1 transaction" => chạy lại nhiều lần kết quả không đổi.
    Không đụng bảng Ý 1.

Ví dụ:  python solve_y2.py --goc 2024-10 --thang-cuoi 2026-07
"""

import argparse, sqlite3, time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from common import list_parts, read_part, load_dm

LIGHT = ["ID", "SO_SO_BHXH", "MA_KHOI", "TU_NGAY", "DEN_NGAY", "TRANG_THAI", "DM_BHXH_ID"]
HEAVY = ["SO_THE_KCB", "HO_TEN", "NGAY_SINH", "GIOI_TINH", "SO_CMND", "DIA_CHI"]

BC = "BC_HSSV_GIAN_DOAN_THAM_GIA"
TK = "TK_DBHC_HSSV_GIAN_DOAN_THAM_GIA"

DDL = f"""
CREATE TABLE IF NOT EXISTS {BC} (
    NGAY_GOC TEXT NOT NULL, THANG_CUOI TEXT NOT NULL, SO_SO_BHXH TEXT NOT NULL,
    SO_THE_KCB TEXT, HO_TEN TEXT, NGAY_SINH TEXT, GIOI_TINH INTEGER, SO_CMND TEXT, DIA_CHI TEXT,
    THE_GOC_ID INTEGER,
    MA_KHOI_GOC TEXT NOT NULL CHECK (MA_KHOI_GOC IN ('HS', 'SV')),
    LOAI_HSSV TEXT NOT NULL CHECK (LOAI_HSSV IN ('HOC_SINH', 'SINH_VIEN')),
    TU_NGAY_GOC TEXT, DEN_NGAY_GOC TEXT, DM_BHXH_ID_GOC INTEGER,
    MA_DVI_GOC TEXT, TEN_DVI_GOC TEXT, MA_TINH_GOC TEXT, TEN_TINH_GOC TEXT,
    THE_HT_ID INTEGER, MA_KHOI_HT TEXT, TU_NGAY_HT TEXT, DEN_NGAY_HT TEXT, DM_BHXH_ID_HT INTEGER,
    MA_DVI_HT TEXT, TEN_DVI_HT TEXT, MA_TINH_HT TEXT, TEN_TINH_HT TEXT,
    NGAY_BAT_DAU_CUA_SO TEXT NOT NULL, NGAY_KET_THUC_CUA_SO TEXT NOT NULL,
    SO_KHOANG_GIAN_DOAN INTEGER NOT NULL CHECK (SO_KHOANG_GIAN_DOAN >= 0),
    TONG_NGAY_GIAN_DOAN INTEGER NOT NULL CHECK (TONG_NGAY_GIAN_DOAN >= 0),
    SO_THANG_QUY_DOI REAL, NGUONG_NGAY INTEGER NOT NULL DEFAULT 90, NGAY_XU_LY TEXT,
    PRIMARY KEY (NGAY_GOC, THANG_CUOI, SO_SO_BHXH)
);
CREATE INDEX IF NOT EXISTS IDX_BC_GD_TINH ON {BC} (NGAY_GOC, THANG_CUOI, LOAI_HSSV, MA_TINH_GOC);
CREATE INDEX IF NOT EXISTS IDX_BC_GD_NGAY ON {BC} (NGAY_GOC, THANG_CUOI, TONG_NGAY_GIAN_DOAN);
CREATE TABLE IF NOT EXISTS {TK} (
    NGAY_GOC TEXT NOT NULL, THANG_CUOI TEXT NOT NULL, MA_TINH TEXT NOT NULL, TEN_TINH TEXT,
    SL_HOC_SINH_GIAN_DOAN INTEGER NOT NULL DEFAULT 0,
    SL_SINH_VIEN_GIAN_DOAN INTEGER NOT NULL DEFAULT 0,
    TONG_GIAN_DOAN INTEGER NOT NULL DEFAULT 0, NGAY_XU_LY TEXT,
    PRIMARY KEY (NGAY_GOC, THANG_CUOI, MA_TINH)
);
"""

DETAIL_COLS = [
    "NGAY_GOC", "THANG_CUOI", "SO_SO_BHXH", "SO_THE_KCB", "HO_TEN", "NGAY_SINH", "GIOI_TINH", "SO_CMND", "DIA_CHI",
    "THE_GOC_ID", "MA_KHOI_GOC", "LOAI_HSSV", "TU_NGAY_GOC", "DEN_NGAY_GOC", "DM_BHXH_ID_GOC",
    "MA_DVI_GOC", "TEN_DVI_GOC", "MA_TINH_GOC", "TEN_TINH_GOC",
    "THE_HT_ID", "MA_KHOI_HT", "TU_NGAY_HT", "DEN_NGAY_HT", "DM_BHXH_ID_HT",
    "MA_DVI_HT", "TEN_DVI_HT", "MA_TINH_HT", "TEN_TINH_HT",
    "NGAY_BAT_DAU_CUA_SO", "NGAY_KET_THUC_CUA_SO", "SO_KHOANG_GIAN_DOAN", "TONG_NGAY_GIAN_DOAN",
    "SO_THANG_QUY_DOI", "NGUONG_NGAY", "NGAY_XU_LY",
]


def first_of_month(d):
    return pd.Timestamp(d.year, d.month, 1)


def first_of_next_month(d):
    return pd.Timestamp(d.year + (d.month == 12), d.month % 12 + 1, 1)


def _ngay(s):
    """Series datetime -> số nguyên ngày (để cộng/trừ nhanh)."""
    return s.to_numpy().astype("datetime64[D]").astype("int64")


def tim_gian_doan(df, g0, g1, k0, k1):
    """Lõi thuật toán, thuần pandas, dùng cho cả solve_y2 và unit test.

    df  : các thẻ (cột LIGHT), index duy nhất. Hàm tự lọc TRANG_THAI = 1.
    g0,g1: đầu tháng gốc / đầu tháng kế tiếp.  k0,k1: tương tự cho tháng cuối.
    Trả về DataFrame (index = SO_SO_BHXH) của TẤT CẢ ứng viên (chưa lọc ngưỡng) gồm:
      bat_dau, ket_thuc, tong, so_khoang, goc_idx, ht_idx
    (goc_idx / ht_idx là nhãn index của thẻ gốc / thẻ đại diện trong df).
    """
    cot = ["bat_dau", "ket_thuc", "tong", "so_khoang", "goc_idx", "ht_idx"]
    gl = g1 - pd.Timedelta(days=1)
    kl = k1 - pd.Timedelta(days=1)

    df = df[df["TRANG_THAI"] == 1]                                               # (1)
    giao_goc = (df["TU_NGAY"] < g1) & (df["DEN_NGAY"] >= g0)
    giao_cuoi = (df["TU_NGAY"] < k1) & (df["DEN_NGAY"] >= k0)
    hssv_goc = df["MA_KHOI"].isin(["HS", "SV"]) & giao_goc

    ung_vien = set(df.loc[hssv_goc, "SO_SO_BHXH"]) & set(df.loc[giao_cuoi, "SO_SO_BHXH"])   # (2)(3)(4)
    if not ung_vien:
        return pd.DataFrame(columns=cot, index=pd.Index([], name="SO_SO_BHXH"))

    sub = df[df["SO_SO_BHXH"].isin(ung_vien)].copy()
    gg, gc, hg = giao_goc.loc[sub.index], giao_cuoi.loc[sub.index], hssv_goc.loc[sub.index]

    # (5) cửa sổ cá nhân
    bd = sub.loc[gg, "TU_NGAY"].clip(lower=g0).groupby(sub.loc[gg, "SO_SO_BHXH"]).min()
    kt = sub.loc[gc, "DEN_NGAY"].clip(upper=kl).groupby(sub.loc[gc, "SO_SO_BHXH"]).max()
    sub["_bd"] = sub["SO_SO_BHXH"].map(bd)
    sub["_kt"] = sub["SO_SO_BHXH"].map(kt)

    # cắt từng thẻ theo cửa sổ
    sub["_tu"] = sub["TU_NGAY"].where(sub["TU_NGAY"] > sub["_bd"], sub["_bd"])
    sub["_den"] = sub["DEN_NGAY"].where(sub["DEN_NGAY"] < sub["_kt"], sub["_kt"])
    c = sub[sub["_tu"] <= sub["_den"]]

    # (6) gộp khoảng bằng cummax rồi tìm ngày trống
    d = pd.DataFrame({"so": c["SO_SO_BHXH"].to_numpy(), "tu": _ngay(c["_tu"]), "den": _ngay(c["_den"])})
    d = d.sort_values(["so", "tu", "den"], kind="mergesort").reset_index(drop=True)
    cm = d.groupby("so")["den"].cummax()
    prev = cm.groupby(d["so"]).shift(1)
    gap = (d["tu"] - prev - 1).fillna(0).clip(lower=0)
    tong = gap.groupby(d["so"]).sum().astype("int64")
    so_khoang = (gap > 0).groupby(d["so"]).sum().astype("int64")

    # thẻ gốc: DEN_NGAY muộn nhất, TU_NGAY muộn nhất, SV trước HS, ID lớn nhất (như solve.py)
    goc = sub[hg].copy()
    goc["_sv"] = np.where(goc["MA_KHOI"] == "SV", 0, 1)
    goc = (goc.sort_values(["SO_SO_BHXH", "DEN_NGAY", "TU_NGAY", "_sv", "ID"],
                           ascending=[True, False, False, True, False])
           .drop_duplicates("SO_SO_BHXH", keep="first"))

    # thẻ đại diện tháng cuối: ngày phủ muộn nhất (cắt cuối tháng), TU_NGAY muộn nhất, ID lớn nhất
    ht = sub[gc].copy()
    ht["_phu"] = ht["DEN_NGAY"].clip(upper=kl)
    ht = (ht.sort_values(["SO_SO_BHXH", "_phu", "TU_NGAY", "ID"],
                         ascending=[True, False, False, False])
          .drop_duplicates("SO_SO_BHXH", keep="first"))

    out = pd.DataFrame({"bat_dau": bd, "ket_thuc": kt})
    out["tong"] = tong.reindex(out.index).fillna(0).astype("int64")
    out["so_khoang"] = so_khoang.reindex(out.index).fillna(0).astype("int64")
    out["goc_idx"] = pd.Series(goc.index.to_numpy(), index=goc["SO_SO_BHXH"].to_numpy()).reindex(out.index)
    out["ht_idx"] = pd.Series(ht.index.to_numpy(), index=ht["SO_SO_BHXH"].to_numpy()).reindex(out.index)
    out.index.name = "SO_SO_BHXH"
    return out[cot]


def _fmt(s):
    return s.dt.strftime("%Y-%m-%d").to_numpy()


def process_part(path, goc, cuoi, dm_idx, nguong, ngay_xu_ly):
    g0, g1 = first_of_month(goc), first_of_next_month(goc)
    k0, k1 = first_of_month(cuoi), first_of_next_month(cuoi)

    df = read_part(path, LIGHT)                       # index = vị trí dòng trong part
    kq = tim_gian_doan(df, g0, g1, k0, k1)
    kq = kq[kq["tong"] >= nguong]
    if kq.empty:
        return None

    goc_c = df.loc[kq["goc_idx"].to_numpy()]
    ht_c = df.loc[kq["ht_idx"].to_numpy()]
    heavy = read_part(path, HEAVY).iloc[kq["goc_idx"].to_numpy().astype(int)]   # cột nặng chỉ cho dòng kết quả

    out = pd.DataFrame({
        "NGAY_GOC": g0.strftime("%Y-%m-%d"), "THANG_CUOI": k0.strftime("%Y-%m-%d"),
        "SO_SO_BHXH": kq.index.to_numpy(),
        "SO_THE_KCB": heavy["SO_THE_KCB"].to_numpy(), "HO_TEN": heavy["HO_TEN"].to_numpy(),
        "NGAY_SINH": pd.to_datetime(heavy["NGAY_SINH"]).dt.strftime("%Y-%m-%d").to_numpy(),
        "GIOI_TINH": heavy["GIOI_TINH"].to_numpy(), "SO_CMND": heavy["SO_CMND"].to_numpy(),
        "DIA_CHI": heavy["DIA_CHI"].to_numpy(),
        "THE_GOC_ID": goc_c["ID"].to_numpy(), "MA_KHOI_GOC": goc_c["MA_KHOI"].to_numpy(),
        "LOAI_HSSV": np.where(goc_c["MA_KHOI"].to_numpy() == "HS", "HOC_SINH", "SINH_VIEN"),
        "TU_NGAY_GOC": _fmt(goc_c["TU_NGAY"]), "DEN_NGAY_GOC": _fmt(goc_c["DEN_NGAY"]),
        "DM_BHXH_ID_GOC": goc_c["DM_BHXH_ID"].to_numpy(),
    })
    dg = dm_idx.reindex(out["DM_BHXH_ID_GOC"].to_numpy())
    out["MA_DVI_GOC"] = dg["MA_DVI"].to_numpy()
    out["TEN_DVI_GOC"] = dg["TEN_DVI"].to_numpy()
    out["MA_TINH_GOC"] = dg["MA_TINH"].fillna("XX").to_numpy()
    out["TEN_TINH_GOC"] = dg["TEN_TINH"].fillna("Không xác định").to_numpy()

    out["THE_HT_ID"] = ht_c["ID"].to_numpy()
    out["MA_KHOI_HT"] = ht_c["MA_KHOI"].to_numpy()
    out["TU_NGAY_HT"] = _fmt(ht_c["TU_NGAY"])
    out["DEN_NGAY_HT"] = _fmt(ht_c["DEN_NGAY"])
    out["DM_BHXH_ID_HT"] = ht_c["DM_BHXH_ID"].to_numpy()
    dh = dm_idx.reindex(out["DM_BHXH_ID_HT"].to_numpy())
    out["MA_DVI_HT"] = dh["MA_DVI"].to_numpy()
    out["TEN_DVI_HT"] = dh["TEN_DVI"].to_numpy()
    out["MA_TINH_HT"] = dh["MA_TINH"].fillna("XX").to_numpy()
    out["TEN_TINH_HT"] = dh["TEN_TINH"].fillna("Không xác định").to_numpy()

    out["NGAY_BAT_DAU_CUA_SO"] = _fmt(kq["bat_dau"])
    out["NGAY_KET_THUC_CUA_SO"] = _fmt(kq["ket_thuc"])
    out["SO_KHOANG_GIAN_DOAN"] = kq["so_khoang"].to_numpy()
    out["TONG_NGAY_GIAN_DOAN"] = kq["tong"].to_numpy()
    out["SO_THANG_QUY_DOI"] = np.round(kq["tong"].to_numpy() / 30, 2)
    out["NGUONG_NGAY"] = nguong
    out["NGAY_XU_LY"] = ngay_xu_ly
    return out[DETAIL_COLS]


def to_rows(df):
    return df.astype(object).where(pd.notna(df), None).values.tolist()


def export_csv(con, out_dir, goc, cuoi):
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"goc{goc:%Y%m}_cuoi{cuoi:%Y%m}"
    params = (first_of_month(goc).strftime("%Y-%m-%d"), first_of_month(cuoi).strftime("%Y-%m-%d"))
    files = []
    for loai, name in (("HOC_SINH", "ds_hoc_sinh_gian_doan_tham_gia"), ("SINH_VIEN", "ds_sinh_vien_gian_doan_tham_gia")):
        f = out_dir / f"{name}_{tag}.csv"
        q = (f"SELECT * FROM {BC} WHERE NGAY_GOC=? AND THANG_CUOI=? AND LOAI_HSSV=? "
             "ORDER BY MA_TINH_GOC, SO_SO_BHXH")
        pd.read_sql_query(q, con, params=params + (loai,)).to_csv(f, index=False, encoding="utf-8-sig")
        files.append(f)
    f = out_dir / f"tk_dbhc_hssv_gian_doan_tham_gia_{tag}.csv"
    pd.read_sql_query(f"SELECT * FROM {TK} WHERE NGAY_GOC=? AND THANG_CUOI=? ORDER BY TONG_GIAN_DOAN DESC, MA_TINH",
                      con, params=params).to_csv(f, index=False, encoding="utf-8-sig")
    files.append(f)
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="data")
    ap.add_argument("--db", default="warehouse.db")
    ap.add_argument("--out", default="output_y2")
    ap.add_argument("--goc", default="2024-10", help="tháng gốc YYYY-MM")
    ap.add_argument("--thang-cuoi", default="2026-07", help="tháng hiện tại YYYY-MM")
    ap.add_argument("--nguong", type=int, default=90, help="ngưỡng gián đoạn (ngày), mặc định 90")
    ap.add_argument("--no-export", action="store_true", help="không xuất CSV")
    a = ap.parse_args()

    goc = datetime.strptime(a.goc, "%Y-%m").date()
    cuoi = datetime.strptime(a.thang_cuoi, "%Y-%m").date()
    parts = list_parts(a.data)
    if not parts:
        raise SystemExit(f"Không thấy dữ liệu trong '{a.data}/ST_INTHE_DTL'. KHÔNG chạy gen_data.py nếu data đã có; kiểm tra đường dẫn --data.")
    dm = load_dm(a.data)
    dm_idx = dm.set_index("ID")
    ngay_xu_ly = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    k_goc = first_of_month(goc).strftime("%Y-%m-%d")
    k_cuoi = first_of_month(cuoi).strftime("%Y-%m-%d")

    con = sqlite3.connect(a.db)
    con.isolation_level = None                       # tự quản lý transaction
    con.executescript(DDL)
    if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='DM_BHXH'").fetchone():
        dm[["ID", "MA_DVI", "TEN_DVI", "MA_CHA", "MA_TINH", "TEN_TINH"]].to_sql("DM_BHXH", con, index=False)

    t0, n_total = time.time(), 0
    con.execute("BEGIN")
    try:
        con.execute(f"DELETE FROM {BC} WHERE NGAY_GOC=? AND THANG_CUOI=?", (k_goc, k_cuoi))
        con.execute(f"DELETE FROM {TK} WHERE NGAY_GOC=? AND THANG_CUOI=?", (k_goc, k_cuoi))
        ins = f"INSERT INTO {BC} ({','.join(DETAIL_COLS)}) VALUES ({','.join('?' * len(DETAIL_COLS))})"
        for n, p in enumerate(parts, 1):
            res = process_part(p, goc, cuoi, dm_idx, a.nguong, ngay_xu_ly)
            if res is not None:
                con.executemany(ins, to_rows(res))
                n_total += len(res)
            print(f"[{n}/{len(parts)}] {p.name}: +{0 if res is None else len(res):,} | "
                  f"tích lũy {n_total:,} | {time.time()-t0:,.0f}s", flush=True)
        con.execute(f"""
            INSERT INTO {TK}
            SELECT ?, ?, t.MA_DVI, t.TEN_DVI,
                   COALESCE(SUM(CASE WHEN b.LOAI_HSSV='HOC_SINH'  THEN 1 ELSE 0 END), 0),
                   COALESCE(SUM(CASE WHEN b.LOAI_HSSV='SINH_VIEN' THEN 1 ELSE 0 END), 0),
                   COUNT(b.SO_SO_BHXH), ?
              FROM DM_BHXH t
              LEFT JOIN {BC} b
                     ON b.MA_TINH_GOC = t.MA_DVI AND b.NGAY_GOC = ? AND b.THANG_CUOI = ?
             WHERE t.MA_CHA = '00'
             GROUP BY t.MA_DVI, t.TEN_DVI
        """, (k_goc, k_cuoi, ngay_xu_ly, k_goc, k_cuoi))
        con.execute("COMMIT")
    except BaseException:
        con.execute("ROLLBACK")                      # lỗi giữa chừng => không để lại dữ liệu dở dang
        raise

    rows = con.execute(f"""SELECT MA_TINH, TEN_TINH, SL_HOC_SINH_GIAN_DOAN, SL_SINH_VIEN_GIAN_DOAN, TONG_GIAN_DOAN
                           FROM {TK} WHERE NGAY_GOC=? AND THANG_CUOI=?
                           ORDER BY TONG_GIAN_DOAN DESC""", (k_goc, k_cuoi)).fetchall()
    tot = [sum(r[i] for r in rows) for i in (2, 3, 4)]
    print(f"\n=== TỔNG HỢP (gốc {k_goc[:7]} -> tháng cuối {k_cuoi[:7]}, gián đoạn >= {a.nguong} ngày) ===")
    print(f"{'Mã':<4}{'Tỉnh/TP':<28}{'Học sinh':>12}{'Sinh viên':>12}{'Tổng':>12}")
    for r in rows[:10]:
        print(f"{r[0]:<4}{r[1]:<28}{r[2]:>12,}{r[3]:>12,}{r[4]:>12,}")
    if len(rows) > 10:
        print(f"... (còn {len(rows)-10} tỉnh/TP, xem file CSV / bảng {TK})")
    print(f"{'':<4}{'TỔNG CỘNG':<28}{tot[0]:>12,}{tot[1]:>12,}{tot[2]:>12,}")

    n_chi_tiet = con.execute(f"SELECT COUNT(*) FROM {BC} WHERE NGAY_GOC=? AND THANG_CUOI=?", (k_goc, k_cuoi)).fetchone()[0]
    print(f"Đối chiếu: chi tiết {n_chi_tiet:,} dòng, thống kê {tot[2]:,} người", "-> KHỚP" if n_chi_tiet == tot[2]
          else "-> LỆCH (có người thuộc cơ quan không nằm trong DM_BHXH, mã tỉnh 'XX')")

    if not a.no_export:
        for f in export_csv(con, Path(a.out), goc, cuoi):
            print("Đã xuất:", f)
    con.close()


if __name__ == "__main__":
    main()
