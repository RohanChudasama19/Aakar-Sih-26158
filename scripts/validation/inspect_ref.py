import trimesh
import sys
import os
import open3d as o3d
import numpy as np
from pathlib import Path

path = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AAKAR-SIH26158-Surface-Fix\aakar\data_external\mars_lvig\raw\HKairport01\reference\cloud_merged.ply")
if not path.exists():
    print(f"NOT FOUND: {path}")
    sys.exit(1)

size_mb = path.stat().st_size / (1024 * 1024)
print(f"File size: {size_mb:.2f} MB")

cloud = o3d.io.read_point_cloud(str(path))
pts = np.asarray(cloud.points)
print(f"Points: {len(pts)}")
if len(pts) > 0:
    vmin, vmax = pts.min(axis=0), pts.max(axis=0)
    print(f"BBox min: {vmin}")
    print(f"BBox max: {vmax}")

print(f"Has colors: {cloud.has_colors()}")
print(f"Has normals: {cloud.has_normals()}")
