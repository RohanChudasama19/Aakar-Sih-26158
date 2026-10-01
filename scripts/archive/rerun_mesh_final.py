import json
from pathlib import Path
import trimesh
import numpy as np

from app.pipeline.mesh import build_mesh

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
ply_10 = work_dir / "dense_10_source_full/fused.ply"

geo = json.loads((work_dir / "alignment.json").read_text())
poses = json.loads((work_dir / "poses.json").read_text())

# fix poses
poses_np = {k: np.array(v) for k, v in poses.items()}
sfm = {"poses": poses_np}

pc = trimesh.load(str(ply_10))
xyz = np.asarray(pc.vertices)
rgb = np.asarray(pc.colors[:,:3]) if pc.colors is not None else np.zeros_like(xyz)

options = {"max_points": 5000000}

print("Running build_mesh with repaired implementation...")
mesh, report = build_mesh(xyz, rgb, geo, sfm, None, None, out_dir=None, options=options)

print("Report from build_mesh:")
print(json.dumps(report, indent=2))
mesh.export("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_10_source_full/mesh_repaired.ply")

