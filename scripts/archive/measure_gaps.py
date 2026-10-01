import numpy as np
import trimesh
import json
from pathlib import Path
from scipy.spatial import cKDTree

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
mesh = trimesh.load(str(work_dir / "dense_10_source_full/mesh_raw.ply"))
geo = json.loads((work_dir / "alignment.json").read_text())

pts = np.asarray(mesh.vertices)
faces = np.asarray(mesh.faces)

# find connected components
edges = mesh.edges_unique
import open3d as o3d
o3d_mesh = o3d.geometry.TriangleMesh()
o3d_mesh.vertices = o3d.utility.Vector3dVector(pts)
o3d_mesh.triangles = o3d.utility.Vector3iVector(faces)
cc_indices, cc_counts, _ = o3d_mesh.cluster_connected_triangles()
cc_indices = np.asarray(cc_indices)

# identify largest component
largest_c = np.argmax(cc_counts)

# extract disconnected components
for i in range(len(cc_counts)):
    if i == largest_c:
        continue
    c_faces = faces[cc_indices == i]
    c_pts = pts[np.unique(c_faces)]
    min_b = c_pts.min(axis=0)
    max_b = c_pts.max(axis=0)
    print(f"Component {i}: {len(c_faces)} faces")
    print(f"  Bounds: min {min_b}, max {max_b}")
