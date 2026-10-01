import os
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

class ProgressStub:
    def __call__(self, val, msg):
        print(f"[{val}%] {msg}")

t0 = time.monotonic()
mesh_path, mesh_metrics = build_mesh(
    points=points,
    colors=colors,
    directory=work_dir,
    profile=FAST_QUALITY_V1["mesh_settings"],
    progress=ProgressStub()
)
runtime = time.monotonic() - t0

print(f"Runtime: {runtime:.1f}s")
print(f"Mesh path: {mesh_path}")
print("Metrics:")
for k, v in mesh_metrics.items():
    print(f"  {k}: {v}")
