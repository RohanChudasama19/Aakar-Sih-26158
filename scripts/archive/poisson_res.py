import numpy as np
import open3d as o3d
from pathlib import Path

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
mesh = o3d.io.read_triangle_mesh(str(work_dir / "dense_10_source_full/mesh_raw.ply"))
pts = np.asarray(mesh.vertices)
min_pt = pts.min(axis=0)
max_pt = pts.max(axis=0)
extents = max_pt - min_pt
print(f"Mesh bounds: Min {min_pt}, Max {max_pt}")
print(f"Extents: {extents}")
