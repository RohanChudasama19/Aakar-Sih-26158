import sys
import time
from pathlib import Path
import json

from app.pipeline.sfm_backend import execute_sfm

def dummy_progress(pct, msg):
    print(f"[{pct}%] {msg}")
    sys.stdout.flush()

work_dir = Path("data/test_dense_fix_3/work")
frames_dir = work_dir / "frames"

with open(work_dir / "preprocess.json", "r") as f:
    info = json.load(f)

opts = {"profile": "FAST_QUALITY"}
geo = {"method": "NONE"}

print("Running execute_sfm...")
t0 = time.monotonic()
try:
    sfm = execute_sfm(
        info=info,
        directory=frames_dir,
        work_dir=work_dir,
        options=opts,
        geo=geo,
        progress=dummy_progress
    )
    t1 = time.monotonic()
    print(f"SfM runtime: {t1 - t0:.2f}s")
    
    reports_dir = work_dir / "outputs/reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    with open(reports_dir / "sfm_report.json", "w") as f:
        json.dump(sfm, f, indent=2)
except Exception as e:
    import traceback
    traceback.print_exc()
