import json
import numpy as np
from pathlib import Path
import open3d as o3d
from app.pipeline.georef import transform

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
ply_10 = work_dir / "dense_10_source_full/fused.ply"
geo = json.loads((work_dir / "alignment.json").read_text())

pc = o3d.io.read_point_cloud(str(ply_10))
xyz = np.asarray(pc.points)
print(f"COLMAP frame extent: {np.linalg.norm(xyz.max(axis=0) - xyz.min(axis=0)):.2f}")

def apply_geo(pts):
    pts = np.asarray(pts)
    s = geo["scale"]
    R = np.array(geo["rotation"])
    t = np.array(geo["translation"])
    origin = np.array(geo["origin"])
    return (pts * s) @ R.T + t - origin

local = apply_geo(xyz)
print(f"Georef frame extent: {np.linalg.norm(local.max(axis=0) - local.min(axis=0)):.2f}")
print(f"Georef Scale applied: {geo['scale']:.2f}")

