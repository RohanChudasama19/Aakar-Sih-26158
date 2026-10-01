import open3d as o3d
import numpy as np
from pathlib import Path

path = Path(r"workspace\HKairport01_FAST_C_FINAL\work\dense_fast\fused.ply")
cloud = o3d.io.read_point_cloud(str(path))
pts = np.asarray(cloud.points)
print(f"Points: {len(pts)}")
if len(pts) > 0:
    vmin, vmax = pts.min(axis=0), pts.max(axis=0)
    print(f"BBox min: {vmin}")
    print(f"BBox max: {vmax}")

import json
align = Path(r"workspace\HKairport01_FAST_C_FINAL\work\alignment.json")
if align.exists():
    with open(align) as f:
        print("alignment.json:", f.read())
