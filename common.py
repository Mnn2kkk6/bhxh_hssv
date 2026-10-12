"""Hàm dùng chung cho gen_data.py / solve.py / verify.py"""
from pathlib import Path
import pandas as pd

TABLE = "ST_INTHE_DTL"
SCEN_TABLE = "SCENARIO"
DATE_COLS = ["NGAY_SINH", "TU_NGAY", "DEN_NGAY"]
STR_COLS = {"SO_SO_BHXH": str, "SO_THE_KCB": str, "SO_CMND": str}


def list_parts(data_dir, table=TABLE):
    """Trả về danh sách file part (parquet hoặc csv) của một bảng."""
    folder = Path(data_dir) / table
    files = sorted(folder.glob("part_*.parquet")) + sorted(folder.glob("part_*.csv"))
    return files


def read_part(path, columns=None):
    """Đọc một part, chỉ lấy các cột cần thiết (tiết kiệm RAM)."""
    path = Path(path)
    if path.suffix == ".parquet":
        return pd.read_parquet(path, columns=columns)
    header = list(pd.read_csv(path, nrows=0).columns)
    wanted = columns if columns is not None else header
    dates = [c for c in DATE_COLS if c in wanted and c in header]
    dtype = {k: v for k, v in STR_COLS.items() if k in wanted and k in header}
    return pd.read_csv(path, usecols=columns, dtype=dtype, parse_dates=dates)


def load_dm(data_dir):
    """Đọc DM_BHXH và suy ra mã tỉnh cho từng cơ quan (huyện trỏ lên tỉnh qua MA_CHA)."""
    dm = pd.read_csv(Path(data_dir) / "DM_BHXH.csv", dtype={"MA_DVI": str, "MA_CHA": str})
    is_tinh = dm["MA_CHA"] == "00"           # cấp tỉnh có MA_CHA = '00' (BHXH Việt Nam)
    dm["MA_TINH"] = dm["MA_DVI"].where(is_tinh, dm["MA_CHA"])
    ten_tinh = dm.loc[is_tinh].set_index("MA_DVI")["TEN_DVI"]
    dm["TEN_TINH"] = dm["MA_TINH"].map(ten_tinh)
    return dm
