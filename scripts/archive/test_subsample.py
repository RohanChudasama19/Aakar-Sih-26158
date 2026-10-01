import json
import trimesh
import numpy as np
import scipy.spatial
from pathlib import Path
from app.pipeline.georef import transform

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
ply_10 = work_dir / "dense_10_source_full/fused.ply"
geo = json.loads((work_dir / "alignment.json").read_text())

pc = trimesh.load(str(ply_10))
xyz = np.asarray(pc.vertices)

def apply_geo(pts):
    pts = np.asarray(pts)
    s = geo["scale"]
    R = np.array(geo["rotation"])
    t = np.array(geo["translation"])
    origin = np.array(geo["origin"])
    return (pts * s) @ R.T + t - origin

local = apply_geo(xyz)

# RANDOMLY SUBSAMPLE TO 150k
max_points = 150000
if len(local) > max_points:
    indices = np.random.default_rng(42).choice(len(local), max_points, replace=False)
    local_sub = local[indices]
else:
    local_sub = local

extent = float(np.linalg.norm(np.ptp(local_sub, axis=0)))
tree_sub = scipy.spatial.cKDTree(local_sub)
nn_sub = tree_sub.query(local_sub, k=2)[0][:, 1]
spacing_sub = max(float(np.median(nn_sub[nn_sub > 0])), extent * 1e-6)

print(f"SUBSAMPLED SPACING: {spacing_sub:.4f}")

strong_thresh = spacing_sub * 5
weak_thresh = spacing_sub * 15
print(f"Strong thresh: {strong_thresh:.4f}")
print(f"Weak thresh: {weak_thresh:.4f}")
