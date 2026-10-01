import json
import csv
import numpy as np
from pathlib import Path

# Load GPS / RTK
input_dir = Path("workspace/HKairport01_FAST_C_FINAL/inputs").absolute()
rtk_path = input_dir / "rtk.csv"
gps_path = input_dir / "gps.csv"

from app.schemas import telemetry
gps_data = telemetry(gps_path)

has_rtk = rtk_path.exists()
print(f"Has RTK: {has_rtk}")

if not has_rtk:
    print("RTK missing!")
else:
    with open(rtk_path) as f:
        rtk_rows = list(csv.DictReader(f))
    print(f"samples: {len(rtk_rows)}")
    if len(rtk_rows) > 0:
        keys = list(rtk_rows[0].keys())
        print(f"Keys: {keys}")

# Let's match timestamps
with open("data_external/mars_lvig/processed/HKairport01/FAST/frames.csv") as f:
    fast_frames = list(csv.DictReader(f))
fast_times = np.array([float(r["timestamp"]) for r in fast_frames])

gps_times = np.array([float(r["time"]) for r in gps_data])
print(f"coverage: {gps_times[-1] - gps_times[0]:.1f} sec")
    
# Sync error
errors = []
for ft in fast_times:
    idx = np.searchsorted(gps_times, ft)
    if idx == 0:
        err = gps_times[0] - ft
    elif idx == len(gps_times):
        err = ft - gps_times[-1]
    else:
        err = min(ft - gps_times[idx-1], gps_times[idx] - ft)
    errors.append(err)

errors = np.array(errors)
print(f"matched FAST_C frames: {len(fast_times)}")
print(f"mean sync error: {np.mean(errors):.6f} sec")
print(f"P95 sync error: {np.percentile(errors, 95):.6f} sec")
