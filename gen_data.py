"""
Sinh Fake Data BHYT theo VÒNG ĐỜI người tham gia (Person Lifecycle).

Mỗi người có 1-2 "giai đoạn" (segment); mỗi giai đoạn là chuỗi thẻ nối tiếp nhau
(chu kỳ 1/3/6/12 tháng). Dữ liệu tính theo chỉ số tháng: 0 = 01/2024 ... 31 = 08/2026.

Kết quả (trong thư mục --out, mặc định ./data):
  DM_BHXH.csv                     danh mục cơ quan BHXH (63 tỉnh + các cơ sở)
  ST_INTHE_DTL/part_00000.parquet bảng thẻ (chia mảnh theo khoảng người)
  SCENARIO/part_00000.parquet     "đáp án" kịch bản cho từng người (dùng để kiểm chứng)

Cùng --persons và --seed => dữ liệu GIỐNG HỆT nhau (hai người dùng chung một bộ).
"""
import argparse, json, shutil, time
from pathlib import Path
import numpy as np
import pandas as pd

KH = np.array(["HS", "SV", "DN", "GD", "TE", "HT"], dtype=object)
M64 = (1 << 64) - 1

PROVINCES = [  # (tên, trọng số dân số tương đối)
    ("Hà Nội", 10), ("Hải Phòng", 6), ("Quảng Ninh", 4), ("Hải Dương", 4), ("Hưng Yên", 3),
    ("Thái Bình", 4), ("Hà Nam", 2), ("Nam Định", 4), ("Ninh Bình", 3), ("Vĩnh Phúc", 3),
    ("Bắc Ninh", 3), ("Bắc Giang", 4), ("Phú Thọ", 4), ("Thái Nguyên", 3), ("Bắc Kạn", 1),
    ("Cao Bằng", 1), ("Lạng Sơn", 2), ("Tuyên Quang", 2), ("Hà Giang", 2), ("Lào Cai", 2),
    ("Yên Bái", 2), ("Lai Châu", 1), ("Điện Biên", 2), ("Sơn La", 3), ("Hòa Bình", 2),
    ("Thanh Hóa", 8), ("Nghệ An", 7), ("Hà Tĩnh", 3), ("Quảng Bình", 2), ("Quảng Trị", 2),
    ("Thừa Thiên Huế", 3), ("Đà Nẵng", 4), ("Quảng Nam", 4), ("Quảng Ngãi", 3), ("Bình Định", 4),
    ("Phú Yên", 2), ("Khánh Hòa", 3), ("Ninh Thuận", 1), ("Bình Thuận", 3), ("Kon Tum", 1),
    ("Gia Lai", 3), ("Đắk Lắk", 4), ("Đắk Nông", 2), ("Lâm Đồng", 3), ("TP Hồ Chí Minh", 12),
    ("Bình Phước", 2), ("Bình Dương", 6), ("Đồng Nai", 7), ("Tây Ninh", 3), ("Bà Rịa - Vũng Tàu", 3),
    ("Long An", 3), ("Tiền Giang", 4), ("Bến Tre", 3), ("Trà Vinh", 2), ("Vĩnh Long", 2),
    ("Đồng Tháp", 3), ("An Giang", 4), ("Kiên Giang", 3), ("Cần Thơ", 3), ("Hậu Giang", 1),
    ("Sóc Trăng", 2), ("Bạc Liêu", 2), ("Cà Mau", 3),
]
HO = np.array(["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng",
               "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"], dtype=object)
DEM_NAM = np.array(["Văn", "Đức", "Minh", "Quang", "Hữu", "Công", "Xuân", "Hoàng", "Thanh", "Gia"], dtype=object)
DEM_NU = np.array(["Thị", "Ngọc", "Thu", "Hoài", "Phương", "Khánh", "Bảo", "Mai", "Thùy", "Diệu"], dtype=object)
TEN_NAM = np.array(["Anh", "Bình", "Cường", "Dũng", "Hải", "Hiếu", "Hùng", "Khoa", "Long", "Nam",
                    "Phúc", "Quân", "Sơn", "Thắng", "Tuấn", "Việt"], dtype=object)
TEN_NU = np.array(["Anh", "Chi", "Dung", "Giang", "Hà", "Hằng", "Hoa", "Lan", "Linh", "Mai",
                   "Ngọc", "Nhung", "Phương", "Thảo", "Trang", "Vy"], dtype=object)
# khoảng tuổi (tại 01/10/2024) theo khối: HS, SV, DN, GD, TE, HT
AGE_MIN = np.array([6, 18, 22, 20, 0, 60])
AGE_MAX = np.array([18, 25, 60, 70, 6, 85])

MONTH_START = (np.datetime64("2024-01", "M") + np.arange(0, 120).astype("timedelta64[M]")).astype("datetime64[D]")


def rnd(ids, salt, seed):
    """Số ngẫu nhiên [0,1) xác định theo (id, salt, seed) - không phụ thuộc kích thước chunk."""
    with np.errstate(over="ignore"):
        x = ids.astype(np.uint64) * np.uint64(0x9E3779B97F4A7C15)
        x = x + np.uint64(((salt + 1) * 0xBF58476D1CE4E5B9 + (seed + 1) * 0x94D049BB133111EB) & M64)
        x ^= x >> np.uint64(30)
        x *= np.uint64(0xBF58476D1CE4E5B9)
        x ^= x >> np.uint64(27)
        x *= np.uint64(0x94D049BB133111EB)
        x ^= x >> np.uint64(31)
    return (x >> np.uint64(11)).astype(np.float64) / float(1 << 53)


def cdiv(a, b):
    """Chia làm tròn lên cho số nguyên."""
    return -((-a) // b)


def build_dm():
    rows, dist = [], []
    nid = 101
    for idx, (name, w) in enumerate(PROVINCES, start=1):
        rows.append((idx, f"{idx:02d}", f"BHXH {name}", "00"))
        for j in range(1, 6 + idx % 5 + 1):
            rows.append((nid, f"{idx:02d}{j:02d}", f"BHXH khu vực {j} - {name}", f"{idx:02d}"))
            dist.append((nid, idx, w, f"Khu vực {j}, {name}"))
            nid += 1
    dm = pd.DataFrame(rows, columns=["ID", "MA_DVI", "TEN_DVI", "MA_CHA"])
    ids = np.array([d[0] for d in dist])
    prov_by_id = np.zeros(nid + 1, dtype=np.int64)
    diaban_by_id = np.empty(nid + 1, dtype=object)
    for d in dist:
        prov_by_id[d[0]] = d[1]
        diaban_by_id[d[0]] = d[3]
    pool = np.repeat(ids, [d[2] for d in dist])
    env = dict(pool=pool, prov_by_id=prov_by_id, diaban_by_id=diaban_by_id,
               first=int(ids.min()), nd=len(ids))
    return dm, env


def gen_chunk(lo, hi, seed, env):
    pid = np.arange(lo, hi, dtype=np.int64) + 1           # người thứ 1..N
    n_p = len(pid)
    r = [rnd(pid, k, seed) for k in range(21)]
    I = lambda a: a.astype(np.int64)

    # ---- 1. Khối chính & kịch bản ------------------------------------------------
    kind = np.select([r[0] < .19, r[0] < .25, r[0] < .55, r[0] < .81, r[0] < .92], [0, 1, 2, 3, 4], 5)
    hssv = kind <= 1
    h_names = ["H1", "H2", "H3a", "H3b", "H4a", "H4b", "H5a", "H5b", "H6", "H7", "H8", "H9"]
    h_cuts = [.28, .50, .57, .60, .66, .70, .75, .78, .84, .87, .89, .96]
    sc_h = np.select([r[1] < c for c in h_cuts], h_names, "H10")
    sc_o = np.select([r[4] < .55, r[4] < .80, r[4] < .88], ["O1", "O2", "O3"], "O4")
    sc = np.where(hssv, sc_h, np.where((kind == 4) & (r[1] < .5), "T1", sc_o))
    isin = lambda names: np.isin(sc, names)

    # ---- 2. Giai đoạn 1: tháng bắt đầu s1, chu kỳ p1, số thẻ n1 ---------------------
    s_base = np.array([0, 0, 3, 6, 8, 9, 9])[I(r[3] * 7)]
    s1 = np.select(
        [sc == "H6", sc == "H7", sc == "T1", sc == "O3", hssv],
        [12 + I(r[3] * 15), I(r[3] * 4), I(r[3] * 11), I(r[3] * 13), s_base],
        default=I(r[3] * 29))
    p_raw = np.where(hssv, np.select([r[2] < .3, r[2] < .6], [3, 6], 12),
                     np.select([r[2] < .55, r[2] < .77, r[2] < .89], [1, 3, 6], 12))
    p1 = np.where(sc == "H7", np.minimum(p_raw, 9 - s1),
                  np.where(~hssv & (sc != "T1"), np.minimum(p_raw, 31 - s1), p_raw))

    nmin = cdiv(10 - s1, p1)            # số thẻ tối thiểu để phủ tháng 10/2024 (m=9)
    nmax30 = (31 - s1) // p1            # tối đa để thẻ cuối hết hạn <= tháng 30
    nmax29 = (30 - s1) // p1
    nmax25 = (26 - s1) // p1
    ncont = cdiv(32 - s1, p1)           # chuỗi phủ tới tháng 31 (08/2026) trở đi
    tgt = np.where(r[5] < .6, np.array([17, 18, 19, 20, 29, 30])[I(r[6] * 6)], 9 + I(r[6] * 22))  # mùa hè

    def nstop(cap):
        return np.minimum(np.maximum(np.rint((tgt - s1 + 1) / p1).astype(np.int64), nmin), np.maximum(cap, nmin))

    n1 = np.select(
        [isin(["H1", "H6", "H8", "O1"]), isin(["H2", "H9", "H3a", "H10"]), isin(["H3b", "H4b"]),
         isin(["H5a", "H5b"]), isin(["H4a", "O4", "O2"]), sc == "H7", sc == "O3", sc == "T1"],
        [ncont, nstop(nmax30), nstop(nmax29), nstop(nmax25), 1 + I(r[7] * nmax30),
         1 + I(r[7] * ((9 - s1) // p1)), 1 + I(r[7] * ((24 - s1) // p1)), cdiv(20 - s1, p1)],
        default=0)

    # ---- 3. Giai đoạn 2 (chuyển khối / chuyển địa bàn / gián đoạn rồi quay lại) ----
    cont2 = isin(["H3a", "H3b", "H4a", "H4b", "H10", "T1", "O4"])
    gap2 = isin(["H5a", "H5b", "O3"])
    end1 = s1 + n1 * p1
    s2 = np.where(cont2, end1, np.where(gap2, end1 + 2 + I(r[8] * 4), -1))
    k2 = np.select(
        [isin(["H3a", "H3b"]), isin(["H4a", "H4b", "H5a", "O3", "O4"]), sc == "H5b", sc == "H10", sc == "T1"],
        [np.where(r[10] < .5, 2, 3), kind, 3, np.where(kind == 0, 1, 2), 0], default=-1)
    p2w = np.select([isin(["H3a", "H3b", "H5b"]), sc == "T1"],
                    [np.select([r[9] < .35, r[9] < .65, r[9] < .85], [1, 3, 6], 12), 12], default=p1)
    stop2 = isin(["H3b", "H4b"])
    p2 = np.where(stop2, np.maximum(1, np.minimum(p2w, 31 - s2)), p2w)
    n2 = np.where(stop2, 1 + I(rnd(pid, 13, seed) * ((31 - s2) // p2)),
                  np.where(s2 >= 0, np.maximum(0, cdiv(32 - s2, p2)), 0))
    d1 = env["pool"][I(r[11] * len(env["pool"]))]
    d2raw = env["pool"][I(r[12] * len(env["pool"]))]
    transfer = isin(["H4a", "H4b", "O4"])
    d2 = np.where(transfer, np.where(d2raw == d1, (d1 - env["first"] + 1) % env["nd"] + env["first"], d2raw), d1)
    inv = sc == "H8"          # chỉ có thẻ bị hủy
    trap = sc == "H9"         # dừng thật + thẻ hủy "kéo dài" (bẫy cho ai quên lọc TRANG_THAI)

    # ---- 4. Thông tin nhân thân (theo người) ---------------------------------------
    gioi = np.where(r[14] < .5, 1, 2).astype(np.int8)
    ho = HO[I(r[16] ** 2 * len(HO))]
    dem = np.where(gioi == 1, DEM_NAM[I(r[17] * len(DEM_NAM))], DEM_NU[I(r[17] * len(DEM_NU))])
    ten = np.where(gioi == 1, TEN_NAM[I(r[18] * len(TEN_NAM))], TEN_NU[I(r[18] * len(TEN_NU))])
    ho_ten = ho + " " + dem + " " + ten
    days = I(AGE_MIN[kind] * 365 + r[15] * (AGE_MAX[kind] - AGE_MIN[kind]) * 365)
    ngay_sinh = (np.datetime64("2024-10-01") - days.astype("timedelta64[D]")).astype("datetime64[ns]")
    so_so = (1_000_000_000 + pid).astype(str).astype(object)
    cmnd = np.array([None if k in (0, 4) else f"{(p * 7919 + 1000003) % 10**12:012d}"
                     for k, p in zip(kind.tolist(), pid.tolist())], dtype=object)

    # ---- 5. Gộp 2 giai đoạn thành danh sách segment -------------------------------
    m2 = (s2 >= 0) & (n2 > 0)
    pl = np.arange(n_p)
    seg_pi = np.concatenate([pl, pl[m2]])
    seg_no = np.concatenate([np.ones(n_p, np.int64), np.full(m2.sum(), 2, np.int64)])
    seg_k = np.concatenate([kind, k2[m2]])
    seg_s = np.concatenate([s1, s2[m2]])
    seg_p = np.concatenate([p1, p2[m2]])
    seg_n = np.concatenate([n1, n2[m2]])
    seg_d = np.concatenate([d1, d2[m2]])
    seg_inv = np.concatenate([inv, np.zeros(m2.sum(), bool)])
    seg_trap = np.concatenate([trap, np.zeros(m2.sum(), bool)])
    seg_pid = pid[seg_pi]

    prov = env["prov_by_id"][seg_d]
    so_the_seg = np.array([f"{KH[k]}4{pv:02d}{p:010d}" for k, pv, p in
                           zip(seg_k.tolist(), prov.tolist(), seg_pid.tolist())], dtype=object)
    addr_no = 1 + I(rnd(seg_pid * 2 + seg_no, 20, seed) * 300)
    dia_chi_seg = np.array([f"Số {a}, {d}" for a, d in
                            zip(addr_no.tolist(), env["diaban_by_id"][seg_d].tolist())], dtype=object)

    # ---- 6. Bung từng segment thành các thẻ nối tiếp ------------------------------
    tot = int(seg_n.sum())
    idx = np.repeat(np.arange(len(seg_n)), seg_n)
    i = np.arange(tot) - np.repeat(np.cumsum(seg_n) - seg_n, seg_n)
    tu_m = seg_s[idx] + i * seg_p[idx]
    den_m = tu_m + seg_p[idx] - 1
    pi = seg_pi[idx]
    ids = (pid[pi] * 2 + seg_no[idx] - 1) * 40 + i
    one_day = np.timedelta64(1, "D")

    df = pd.DataFrame({
        "ID": ids,
        "SO_SO_BHXH": so_so[pi],
        "SO_THE_KCB": so_the_seg[idx],
        "HO_TEN": ho_ten[pi],
        "NGAY_SINH": ngay_sinh[pi],
        "GIOI_TINH": gioi[pi],
        "SO_CMND": cmnd[pi],
        "DIA_CHI": dia_chi_seg[idx],
        "MA_KHOI": KH[seg_k][idx],
        "TU_NGAY": MONTH_START[tu_m].astype("datetime64[ns]"),
        "DEN_NGAY": (MONTH_START[den_m + 1] - one_day).astype("datetime64[ns]"),
        "TRANG_THAI": np.where(seg_inv[idx], 0, 1).astype(np.int8),
        "DM_BHXH_ID": seg_d[idx].astype(np.int32),
    })

    # ---- 7. Thẻ hủy: (a) bẫy "kéo dài" cho nhóm H9, (b) ~3% thẻ cấp đổi/hủy -------
    parts = [df]
    trap_m = seg_trap[idx] & (seg_no[idx] == 1) & (i == seg_n[idx] - 1)
    if trap_m.any():
        t = df[trap_m].copy()
        t["ID"] += 10_000_000_000
        t["TRANG_THAI"] = np.int8(0)
        m_end = 32 + I(rnd(pid[pi][trap_m], 19, seed) * 6)          # hết hạn "nhầm" vào tháng 31..36
        t["DEN_NGAY"] = (MONTH_START[m_end] - one_day).astype("datetime64[ns]")
        parts.append(t)
    dup_m = ~seg_inv[idx] & (rnd(ids, 30, seed) < 0.03)
    if dup_m.any():
        d = df[dup_m].copy()
        d["ID"] += 20_000_000_000
        d["TRANG_THAI"] = np.int8(0)
        parts.append(d)
    cards = pd.concat(parts, ignore_index=True)

    expected = np.isin(sc, ["H2", "H3b", "H4b", "H9"])
    scen = pd.DataFrame({"SO_SO_BHXH": so_so, "MA_KHOI_CHINH": KH[kind], "KICH_BAN": sc, "KY_VONG_DUNG": expected})
    return cards, scen


def write(df, path, fmt):
    if fmt == "parquet":
        df.to_parquet(path, index=False)
    else:
        df.to_csv(path, index=False, date_format="%Y-%m-%d")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--persons", type=int, default=200_000, help="số người (20_000_000 ~ 200 triệu thẻ)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--chunk", type=int, default=250_000, help="số người mỗi part")
    ap.add_argument("--out", default="data")
    ap.add_argument("--format", choices=["parquet", "csv"], default="parquet")
    ap.add_argument("--resume", action="store_true", help="bỏ qua part đã có (chạy tiếp khi bị ngắt)")
    a = ap.parse_args()

    out = Path(a.out)
    ext = "parquet" if a.format == "parquet" else "csv"
    dirs = {t: out / t for t in ("ST_INTHE_DTL", "SCENARIO")}
    if not a.resume:
        for d in dirs.values():
            shutil.rmtree(d, ignore_errors=True)
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    dm, env = build_dm()
    dm.to_csv(out / "DM_BHXH.csv", index=False)
    (out / "meta.json").write_text(json.dumps(vars(a), ensure_ascii=False, indent=2), encoding="utf-8")

    t0, total = time.time(), 0
    n_chunks = -(-a.persons // a.chunk)
    for c in range(n_chunks):
        lo, hi = c * a.chunk, min(a.persons, (c + 1) * a.chunk)
        f1 = dirs["ST_INTHE_DTL"] / f"part_{c:05d}.{ext}"
        f2 = dirs["SCENARIO"] / f"part_{c:05d}.{ext}"
        if a.resume and f1.exists() and f2.exists():
            print(f"[{c+1}/{n_chunks}] đã có, bỏ qua")
            continue
        cards, scen = gen_chunk(lo, hi, a.seed, env)
        write(cards, f1, a.format)
        write(scen, f2, a.format)
        total += len(cards)
        print(f"[{c+1}/{n_chunks}] người {lo+1:,}-{hi:,}: {len(cards):,} thẻ | "
              f"tích lũy {total:,} | {time.time()-t0:,.0f}s", flush=True)
    print(f"\nXong. Tổng {total:,} bản ghi thẻ cho {a.persons:,} người -> {out.resolve()}")


if __name__ == "__main__":
    main()
