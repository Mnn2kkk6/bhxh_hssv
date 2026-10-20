import sqlite3, sys

db, path = sys.argv[1], sys.argv[2]
sql = open(path, encoding="utf-8").read()
if "--ddl" in sys.argv:                      # chỉ chạy phần 1 (DDL)
    sql = sql[: sql.index("-- 2. Ghi kết quả")]

con = sqlite3.connect(db)
con.executescript(sql)
con.commit()

print("Bảng:", [r[0] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")])
print("Chỉ mục:", [r[0] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'IDX_BC_GD%'")])
print("Số dòng Ý 1:",
      con.execute("SELECT COUNT(*) FROM BC_HSSV_DUNG_THAM_GIA").fetchone()[0],
      con.execute("SELECT COUNT(*) FROM TK_DBHC_HSSV_DUNG_THAM_GIA").fetchone()[0])
con.close()