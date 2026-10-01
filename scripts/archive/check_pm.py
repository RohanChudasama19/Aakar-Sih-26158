import re
from pathlib import Path

pm_log = Path("data/test_dense_fix_3/work/dense_fast_quality/pm_log.txt")
if not pm_log.exists():
    print("pm_log not found")
    exit(0)

with open(pm_log) as f:
    lines = f.readlines()

print("SOURCE VIEW SUPPORT DIAGNOSTIC")
for line in lines:
    if "src_image_idxs:" in line:
        parts = line.split("src_image_idxs:")[1].strip().split()
        print(f"selected/usable source views: {len(parts)} ({' '.join(parts)})")
