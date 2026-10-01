import sys, sqlite3
from pathlib import Path
db = Path("data/mars_hkairport01_quality/work/colmap.db")
if not db.exists():
    print("DB not found!")
    sys.exit(1)
con = sqlite3.connect(str(db))
cur = con.cursor()
for tbl in ["cameras","images","descriptors","keypoints","matches","two_view_geometries"]:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        n = cur.fetchone()[0]
        print(f"{tbl}: {n}")
    except Exception as e:
        print(f"{tbl}: ERROR {e}")
con.close()