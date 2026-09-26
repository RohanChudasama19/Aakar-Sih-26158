import trimesh
import numpy as np
from pathlib import Path
ply_6 = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_full_ref2/fused.ply")
pc = trimesh.load(str(ply_6))
xyz = np.asarray(pc.vertices)
extents = xyz.max(axis=0) - xyz.min(axis=0)
print(f"6-source extents: {extents[0]:.2f} x {extents[1]:.2f} x {extents[2]:.2f}")
