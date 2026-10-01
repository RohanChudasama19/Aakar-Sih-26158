import os
import json
import time
import trimesh
import numpy as np
from pathlib import Path

from app.pipeline.mesh import build_mesh
from app.pipeline.profiles import FAST_QUALITY_V1

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
dense_dir = work_dir / "dense_full_ref2"
fused_ply = dense_dir / "fused.ply"

pc = trimesh.load(str(fused_ply))
points = np.array(pc.vertices)
colors = np.array(pc.colors) if pc.colors is not None else np.zeros_like(points)

geo = json.loads((work_dir / "alignment.json").read_text())

def qvec2rotmat(qvec):
    return np.array([
        [1 - 2 * qvec[2]**2 - 2 * qvec[3]**2,
         2 * qvec[1] * qvec[2] - 2 * qvec[0] * qvec[3],
         2 * qvec[3] * qvec[1] + 2 * qvec[0] * qvec[2]],
        [2 * qvec[1] * qvec[2] + 2 * qvec[0] * qvec[3],
         1 - 2 * qvec[1]**2 - 2 * qvec[3]**2,
         2 * qvec[2] * qvec[3] - 2 * qvec[0] * qvec[1]],
        [2 * qvec[3] * qvec[1] - 2 * qvec[0] * qvec[2],
         2 * qvec[2] * qvec[3] + 2 * qvec[0] * qvec[1],
         1 - 2 * qvec[1]**2 - 2 * qvec[2]**2]])

sfm = {"poses": {}}
images_txt = work_dir / "sparse_txt/images.txt"
with open(images_txt, "r") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 10 and (parts[9].endswith(".png") or parts[9].endswith(".jpg")):
            qw, qx, qy, qz, tx, ty, tz = map(float, parts[1:8])
            name = parts[9]
            R = qvec2rotmat([qw, qx, qy, qz])
            t = np.array([[tx], [ty], [tz]])
            pose = np.hstack([R, t])
            sfm["poses"][name] = pose

t0 = time.monotonic()
mesh_obj, report = build_mesh(
    points=points,
    colors=colors,
    geo=geo,
    sfm=sfm,
    k=None,
    directory=work_dir / "images",
    out_dir=dense_dir,
    options={
        **FAST_QUALITY_V1["mesh_settings"],
        "max_points": 500000,
        "texture_mesh": False
    }
)
runtime = time.monotonic() - t0

print(f"Runtime: {runtime:.1f}s")
print("Metrics:")
for k, v in report.items():
    print(f"  {k}: {v}")
