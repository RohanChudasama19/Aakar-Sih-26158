import open3d as o3d
import numpy as np
from pathlib import Path
import time

# Sample the MARS reference cloud to assess its quality
p = Path("data_external/mars_lvig/raw/HKairport01/reference/cloud_merged.ply")
print(f"Loading {p.name}...")
t0 = time.monotonic()
pcd = o3d.io.read_point_cloud(str(p))
print(f"Loaded in {time.monotonic()-t0:.1f}s")
pts = np.asarray(pcd.points)
print(f"Total points: {len(pts):,}")
print(f"Bbox min: {pts.min(axis=0)}")
print(f"Bbox max: {pts.max(axis=0)}")
span = pts.max(axis=0) - pts.min(axis=0)
print(f"Span XYZ: {span}")
print(f"Colors present: {len(np.asarray(pcd.colors)) > 0}")
