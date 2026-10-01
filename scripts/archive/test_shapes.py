import trimesh
import numpy as np
from pathlib import Path

fused_ply = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_full_ref2/fused.ply")
pc = trimesh.load(str(fused_ply))
print(f"vertices: {pc.vertices.shape}")
if pc.colors is not None:
    print(f"colors: {pc.colors.shape}")
else:
    print("colors is None")
