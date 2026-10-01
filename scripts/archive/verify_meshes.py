import open3d as o3d
import numpy as np
from pathlib import Path
import json
import hashlib

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
ply_10 = work_dir / "dense_10_source_full/fused.ply"
mesh_raw = work_dir / "dense_10_source_full/mesh_raw.ply"
mesh_repaired = work_dir / "dense_10_source_full/mesh_repaired.ply"

def sha256(path):
    if not path.exists(): return "Missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()

print(f"fused.ply: {sha256(ply_10)}")
print(f"mesh_raw.ply: {sha256(mesh_raw)}")
print(f"mesh_repaired.ply: {sha256(mesh_repaired)}")

mesh = o3d.io.read_triangle_mesh(str(mesh_repaired))
mesh.compute_vertex_normals()

# Calculate connected components
cc_indices, cc_counts, _ = mesh.cluster_connected_triangles()
largest_c = np.argmax(cc_counts)
largest_frac = cc_counts[largest_c] / sum(cc_counts)

print(f"Total faces: {sum(cc_counts)}")
print(f"Largest component: {cc_counts[largest_c]} faces ({largest_frac:.4%})")

