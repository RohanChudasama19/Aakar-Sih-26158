import numpy as np
import trimesh
import json
from pathlib import Path
from scipy.spatial import cKDTree

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
mesh = trimesh.load(str(work_dir / "dense_10_source_full/mesh_repaired.ply"))
pts = np.asarray(mesh.vertices)
faces = np.asarray(mesh.faces)

import open3d as o3d
o3d_mesh = o3d.geometry.TriangleMesh()
o3d_mesh.vertices = o3d.utility.Vector3dVector(pts)
o3d_mesh.triangles = o3d.utility.Vector3iVector(faces)
cc_indices, cc_counts, _ = o3d_mesh.cluster_connected_triangles()
cc_indices = np.asarray(cc_indices)

largest_c = np.argmax(cc_counts)
print(f"Largest Component (0): {cc_counts[largest_c]} faces")
print(f"Total faces: {len(faces)}")
print(f"Largest fraction: {cc_counts[largest_c] / len(faces):.4f}")
print(f"Total components: {len(cc_counts)}")

c_faces = faces[cc_indices == largest_c]
c_pts = pts[np.unique(c_faces)]
largest_tree = cKDTree(c_pts)

for i in [1, 2, 3]:
    if i >= len(cc_counts): break
    idx = np.argsort(cc_counts)[-1-i]
    cf = faces[cc_indices == idx]
    cp = pts[np.unique(cf)]
    dist, _ = largest_tree.query(cp)
    min_dist = np.min(dist)
    print(f"Component {idx} ({len(cf)} faces): distance to largest component = {min_dist:.2f} m")

