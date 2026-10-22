"""
Kiểm thử Ý 2: 20 tình huống T01-T20 (khớp tài liệu test case) + đối chiếu ngẫu nhiên
với cách tính độc lập bằng tập ngày.

Chạy:  python test_y2.py
"""

import random
import sys
from datetime import date, timedelta

import pandas as pd

from solve_y2 import first_of_month, first_of_next_month, tim_gian_doan

G0, G1 = pd.Timestamp(2024, 10, 1), pd.Timestamp(2024, 11, 1)
K0, K1 = pd.Timestamp(2026, 7, 1), pd.Timestamp(2026, 8, 1)
NGUONG = 90

_id = [0]


def the(so, khoi, tu, den, tt=1, id_=None, dm=1):
    """Một thẻ. Ngày viết dạng 'dd/mm/yyyy'."""
    _id[0] += 1
    d = lambda s: pd.Timestamp(datetime_from(s))
    return dict(ID=id_ if id_ is not None else _id[0], SO_SO_BHXH=so, MA_KHOI=khoi,
                TU_NGAY=d(tu), DEN_NGAY=d(den), TRANG_THAI=tt, DM_BHXH_ID=dm)


def datetime_from(s):
    dd, mm, yy = s.split("/")
    return date(int(yy), int(mm), int(dd))


def chay(cards):
    df = pd.DataFrame(cards).reset_index(drop=True)
    return tim_gian_doan(df, G0, G1, K0, K1), df


FAILS = []


def kiem(ten, cards, ky_vong_tong, dat, so="X", **extra):
    """ky_vong_tong=None  -> người đó phải bị loại (không phải ứng viên)."""
    kq, df = chay(cards)
    if ky_vong_tong is None:
        ok = so not in kq.index
        mo_ta = "loại" if ok else f"lẽ ra phải loại, nhưng ra tong={kq.loc[so, 'tong']}"
    else:
        ok = so in kq.index and int(kq.loc[so, "tong"]) == ky_vong_tong and (kq.loc[so, "tong"] >= NGUONG) == dat
        mo_ta = (f"tong={int(kq.loc[so, 'tong'])} ({'đạt' if kq.loc[so,'tong']>=NGUONG else 'không đạt'})"
                 if so in kq.index else "không có trong ứng viên")
    for k, v in extra.items():                         # kiểm tra thêm: thẻ gốc / đại diện / loại
        if so in kq.index:
            got = df.loc[kq.loc[so, "goc_idx" if k == "goc_id" else "ht_idx"], "ID"]
            if got != v:
                ok = False
                mo_ta += f" | {k}: ra ID {got}, mong {v}"
    print(f"{'OK  ' if ok else 'LỖI'} {ten:<4} {mo_ta}")
    if not ok:
        FAILS.append(ten)


def run_unit():
    kiem("T01", [the("X", "HS", "20/10/2024", "31/12/2024"), the("X", "HS", "01/04/2025", "31/07/2026")], 90, True)
    kiem("T02", [the("X", "HS", "20/10/2024", "31/12/2024"), the("X", "HS", "31/03/2025", "31/07/2026")], 89, False)
    kiem("T03", [the("X", "HS", "01/10/2024", "31/12/2024"), the("X", "HS", "01/01/2025", "31/07/2026")], 0, False)
    kiem("T04", [the("X", "HS", "01/10/2024", "31/12/2024"), the("X", "HS", "15/12/2024", "31/07/2026")], 0, False)
    kiem("T05", [the("X", "HS", "01/10/2024", "31/03/2026"), the("X", "DN", "01/01/2025", "28/02/2025"),
                 the("X", "DN", "01/05/2026", "31/07/2026")], 30, False)
    kiem("T06", [the("X", "HS", "01/10/2024", "30/09/2025"), the("X", "DN", "01/10/2025", "31/12/2025", tt=0),
                 the("X", "DN", "01/01/2026", "31/07/2026")], 92, True)
    kiem("T07", [the("X", "HS", "01/10/2024", "31/12/2024"), the("X", "HS", "31/01/2025", "30/06/2025"),
                 the("X", "HS", "31/07/2025", "31/12/2025"), the("X", "HS", "31/01/2026", "31/07/2026")], 90, True)
    kiem("T08", [the("X", "HS", "01/10/2024", "31/12/2024"), the("X", "HS", "31/01/2025", "30/06/2025"),
                 the("X", "HS", "31/07/2025", "31/12/2025"), the("X", "HS", "30/01/2026", "31/07/2026")], 89, False)
    kiem("T09", [the("X", "HS", "20/10/2024", "31/12/2024"), the("X", "HS", "21/03/2025", "31/07/2026")], 79, False)
    kiem("T10", [the("X", "HS", "01/10/2024", "10/04/2026"), the("X", "DN", "01/07/2026", "15/07/2026")], 81, False)
    kiem("T11", [the("X", "HS", "01/10/2024", "30/06/2025"), the("X", "DN", "01/10/2025", "31/07/2026")], 92, True)
    kiem("T12", [the("X", "HS", "01/10/2024", "31/12/2024"), the("X", "HS", "01/04/2025", "30/06/2026")], None, False)
    kiem("T13", [the("X", "DN", "01/10/2024", "31/12/2024"), the("X", "DN", "01/06/2025", "31/07/2026")], None, False)
    kiem("T14a", [the("X", "HS", "01/11/2024", "31/07/2026")], None, False)
    kiem("T14b", [the("X", "HS", "01/07/2024", "30/09/2024"), the("X", "HS", "01/04/2025", "31/07/2026")], None, False)
    kiem("T15", [the("X", "HS", "01/10/2024", "31/12/2024"), the("X", "HS", "01/04/2025", "01/07/2026")], 90, True)
    kiem("T16", [the("X", "HS", "01/10/2024", "31/12/2026")], 0, False)
    kiem("T17", [the("X", "HS", "01/10/2024", "31/12/2025", id_=1),
                 the("X", "HS", "01/01/2026", "31/12/2026", id_=200), the("X", "HS", "01/02/2026", "31/07/2026", id_=100)],
          0, False, ht_id=100)
    kiem("T18", [the("X", "HS", "01/10/2024", "31/01/2026", id_=1),
                 the("X", "HS", "01/02/2026", "31/07/2026", id_=100), the("X", "HS", "01/02/2026", "31/07/2026", id_=200)],
          0, False, ht_id=200)
    kiem("T19", [the("X", "HS", "01/09/2024", "31/12/2024", id_=10), the("X", "SV", "01/10/2024", "31/12/2024", id_=11),
                 the("X", "HS", "01/01/2025", "31/07/2026", id_=12)], 0, False, goc_id=11)
    kiem("T20", [the("X", "HS", "01/10/2024", "30/11/2024"), the("X", "DN", "15/01/2025", "10/04/2025"),
                 the("X", "DN", "01/04/2025", "31/07/2026")], 45, False)


def tinh_doc_lap(cards):
    """Cách tính độc lập: tập ngày được phủ trong cửa sổ cá nhân."""
    hop_le = [c for c in cards if c["TRANG_THAI"] == 1]
    g0, gl, k0, kl = G0.date(), (G1 - pd.Timedelta(days=1)).date(), K0.date(), (K1 - pd.Timedelta(days=1)).date()
    tu = lambda c: c["TU_NGAY"].date()
    den = lambda c: c["DEN_NGAY"].date()
    giao_g = [c for c in hop_le if tu(c) <= gl and den(c) >= g0]
    giao_k = [c for c in hop_le if tu(c) <= kl and den(c) >= k0]
    if not any(c["MA_KHOI"] in ("HS", "SV") for c in giao_g) or not giao_k:
        return None
    bd = min(max(tu(c), g0) for c in giao_g)
    kt = max(min(den(c), kl) for c in giao_k)
    phu = set()
    for c in hop_le:
        a, b = max(tu(c), bd), min(den(c), kt)
        d = a
        while d <= b:
            phu.add(d)
            d += timedelta(days=1)
    return (kt - bd).days + 1 - len(phu)


def run_ngau_nhien(n_nguoi=3000, seed=7):
    rnd = random.Random(seed)
    cards, truth = [], {}
    base = date(2024, 8, 1)
    for i in range(n_nguoi):
        so = f"P{i:05d}"
        ds = []
        cur = base + timedelta(days=rnd.randint(0, 120))
        for _ in range(rnd.randint(1, 6)):
            tu = cur
            den = tu + timedelta(days=rnd.randint(20, 260))
            ds.append(dict(ID=len(cards) + len(ds) + 1, SO_SO_BHXH=so, MA_KHOI=rnd.choice(["HS", "SV", "DN", "GD"]),
                           TU_NGAY=pd.Timestamp(tu), DEN_NGAY=pd.Timestamp(den),
                           TRANG_THAI=0 if rnd.random() < 0.12 else 1, DM_BHXH_ID=rnd.randint(1, 5)))
            cur = den + timedelta(days=rnd.randint(-40, 80))           # chồng lấn / nối tiếp / hở
            if rnd.random() < 0.2:                                      # thêm thẻ lồng
                ds.append(dict(ID=len(cards) + len(ds) + 1, SO_SO_BHXH=so, MA_KHOI="DN",
                               TU_NGAY=pd.Timestamp(tu + timedelta(days=5)),
                               DEN_NGAY=pd.Timestamp(tu + timedelta(days=15)), TRANG_THAI=1, DM_BHXH_ID=1))
        cards.extend(ds)
        truth[so] = tinh_doc_lap(ds)
    df = pd.DataFrame(cards).reset_index(drop=True)
    kq = tim_gian_doan(df, G0, G1, K0, K1)
    ung = {k for k, v in truth.items() if v is not None}
    sai = [s for s in ung if s not in kq.index or int(kq.loc[s, "tong"]) != truth[s]]
    thua = [s for s in kq.index if s not in ung]
    dat = sum(1 for s in ung if truth[s] >= NGUONG)
    ok = not sai and not thua
    print(f"{'OK  ' if ok else 'LỖI'} NGẪU NHIÊN {n_nguoi} người: ứng viên {len(ung)}, đạt ≥{NGUONG}: {dat}, "
          f"sai {len(sai)}, thừa {len(thua)}")
    if not ok:
        FAILS.append("ngau_nhien")


if __name__ == "__main__":
    run_unit()
    run_ngau_nhien()
    print("\nTất cả đạt." if not FAILS else f"\nCó lỗi: {FAILS}")
    sys.exit(1 if FAILS else 0)
