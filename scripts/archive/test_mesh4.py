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

geo = {
    "translation": [0.0, 0.0, 0.0],
    "scale": 1.0,
    "rotation": np.eye(3).tolist(),
    "status": "MOCK"
}

import sys
sys.path.append(str(Path(".").resolve()))
from app.pipeline.sfm_backend import read_cameras_text, read_images_text
imgs = read_images_text(work_dir / "sparse/images.txt")
sfm = {"poses": {}}
for i, img in imgs.items():
    R = img.qvec2rotmat()
    t = img.tvec.reshape(3, 1)
    pose = np.hstack([R, t])
    sfm["poses"][img.name] = pose

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
