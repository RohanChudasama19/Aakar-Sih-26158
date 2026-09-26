import csv
import numpy as np
from pathlib import Path

print("PHASE 2: FRAME OVERLAP ANALYSIS")
mars_dir = Path("data_external/mars_lvig/processed/HKairport01/FAST")
gps_rows = list(csv.DictReader(open(mars_dir / "gps.csv")))
lats = np.array([float(r["latitude"]) for r in gps_rows])
lons = np.array([float(r["longitude"]) for r in gps_rows])
alts = np.array([float(r["altitude_m"]) for r in gps_rows])
lat0, lon0 = lats.mean(), lons.mean()
x = (lons - lon0) * np.cos(np.radians(lat0)) * 111111
y = (lats - lat0) * 111111
z = alts - alts.mean()
positions = np.stack([x, y, z], axis=1)
print(f"Frames: {len(positions)}, Scene: {x.max()-x.min():.1f}m EW x {y.max()-y.min():.1f}m NS x {z.max()-z.min():.1f}m alt")
step_dists = np.linalg.norm(np.diff(positions, axis=0), axis=1)
print(f"Consecutive baseline: min={step_dists.min():.2f}m mean={step_dists.mean():.2f}m max={step_dists.max():.2f}m")
gaps = np.where(step_dists > 5.0)[0]
print(f"Gaps >5m: {len(gaps)}")
for g in gaps[:5]:
    print(f"  Frame {g}->{g+1}: {step_dists[g]:.2f}m")
step_size = len(positions) // 200
selected = list(range(0, len(positions), step_size))[:200]
sel_pos = positions[selected]
sel_d = np.linalg.norm(np.diff(sel_pos, axis=0), axis=1)
print(f"200-frame selection (every {step_size}): baseline min={sel_d.min():.2f}m mean={sel_d.mean():.2f}m max={sel_d.max():.2f}m")
large_gaps = (sel_d > 20.0).sum()
print(f"Large gaps >20m: {large_gaps}")
print(f"Mean altitude: {alts.mean():.1f}m")
if large_gaps == 0 and sel_d.max() < 30:
    print("VERDICT: ADEQUATE -- 200-frame selection is valid")
else:
    print(f"WARNING: {large_gaps} large gaps in selection")