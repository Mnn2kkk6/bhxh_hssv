"""
Đối chiếu độc lập kết quả của solve.py bằng:
  (A) Cách tính thứ hai: quy mọi ngày về "chỉ số tháng" rồi dùng groupby/any (khác hẳn cách lọc ngày + loại trừ)
  (B) Đáp án kịch bản do gen_data.py ghi sẵn (SCENARIO) - biết trước ai thực sự "dừng"
  (C) Tự nhất quán: không trùng người, HS/SV tách riêng, tổng thống kê = tổng chi tiết
  (D) Cho thấy "bẫy": nếu quên lọc TRANG_THAI = 1 thì kết quả lệch bao nhiêu.
"""
import argparse, sqlite3
from datetime import datetime
import pandas as pd
from common import list_parts, read_part


def midx(s):
    return s.dt.year * 12 + s.dt.month


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--db", default="warehouse.db")
    ap.add_argument("--goc", default="2024-10")
    ap.add_argument("--kiem-tra", default="2026-08-10")
    a = ap.parse_args()
    goc = datetime.strptime(a.goc, "%Y-%m").date()
    kt = datetime.strptime(a.kiem_tra, "%Y-%m-%d").date()
    G, N = goc.year * 12 + goc.month, kt.year * 12 + kt.month
    k_goc, k_kt = f"{goc:%Y-%m}-01", f"{kt:%Y-%m-%d}"

    con = sqlite3.connect(a.db)
    bc = pd.read_sql_query("SELECT SO_SO_BHXH, LOAI_HSSV FROM BC_HSSV_DUNG_THAM_GIA WHERE NGAY_GOC=? AND NGAY_KIEM_TRA=?",
                           con, params=(k_goc, k_kt))
    tk_tong = con.execute("SELECT COALESCE(SUM(TONG_DUNG),0) FROM TK_DBHC_HSSV_DUNG_THAM_GIA "
                          "WHERE NGAY_GOC=? AND NGAY_KIEM_TRA=?", (k_goc, k_kt)).fetchone()[0]
    ket_qua = dict(zip(bc["SO_SO_BHXH"], bc["LOAI_HSSV"]))

    alt_set, alt_loai, naive_set = set(), {}, set()
    for p in list_parts(a.data):
        d = read_part(p, ["SO_SO_BHXH", "MA_KHOI", "TU_NGAY", "DEN_NGAY", "TRANG_THAI"])
        d["tu"], d["den"] = midx(d["TU_NGAY"]), midx(d["DEN_NGAY"])
        d["hl"] = d["TRANG_THAI"] == 1
        d["hs"] = d["hl"] & (d["MA_KHOI"] == "HS") & (d["tu"] <= G) & (d["den"] >= G)
        d["sv"] = d["hl"] & (d["MA_KHOI"] == "SV") & (d["tu"] <= G) & (d["den"] >= G)
        d["now"] = d["hl"] & (d["tu"] <= N) & (d["den"] >= N)
        d["now_naive"] = (d["tu"] <= N) & (d["den"] >= N)             # quên lọc TRANG_THAI
        g = d.groupby("SO_SO_BHXH")[["hs", "sv", "now", "now_naive"]].any()
        base = g[g["hs"] | g["sv"]]
        stop = base[~base["now"]]
        alt_set |= set(stop.index)
        naive_set |= set(base[~base["now_naive"]].index)
        for sid, hs, sv in zip(stop.index, stop["hs"], stop["sv"]):
            if hs != sv:                                              # chỉ so khi không mơ hồ
                alt_loai[sid] = "HOC_SINH" if hs else "SINH_VIEN"

    scen = pd.concat([read_part(p) for p in list_parts(a.data, "SCENARIO")])
    truth = set(scen.loc[scen["KY_VONG_DUNG"].astype(str).str.lower() == "true", "SO_SO_BHXH"])

    mine = set(ket_qua)
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"[{'ĐẠT' if cond else 'LỖI'}] {name} {detail}")

    check("(A) Trùng cách tính độc lập", mine == alt_set,
          f"| solve={len(mine):,} alt={len(alt_set):,} lệch={len(mine ^ alt_set):,}")
    mis = sum(1 for s, l in alt_loai.items() if ket_qua.get(s) != l)
    check("(A) Phân loại HS/SV khớp", mis == 0, f"| số dòng lệch={mis:,}")
    check("(B) Khớp đáp án kịch bản sinh dữ liệu", mine == truth,
          f"| thiếu={len(truth - mine):,} thừa={len(mine - truth):,}")
    check("(C) Mỗi người đúng 1 dòng", len(bc) == len(mine), f"| dòng={len(bc):,}")
    check("(C) Tổng bảng thống kê = tổng chi tiết", tk_tong == len(bc), f"| TK={tk_tong:,} CT={len(bc):,}")
    print(f"[i ] Bẫy: nếu quên lọc TRANG_THAI=1 sẽ chỉ ra {len(naive_set):,} người "
          f"(thiếu {len(mine - naive_set):,} người so với đúng)")
    print("\nKẾT LUẬN:", "TẤT CẢ ĐẠT ✔" if ok else "CÓ LỖI ✘")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
