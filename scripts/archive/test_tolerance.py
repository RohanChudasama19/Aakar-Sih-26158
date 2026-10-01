import json
import numpy as np
import scipy.spatial
from pathlib import Path
import open3d as o3d
from app.pipeline.georef import transform

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
ply_10 = work_dir / "dense_10_source_full/fused.ply"
geo = json.loads((work_dir / "alignment.json").read_text())

pc = o3d.io.read_point_cloud(str(ply_10))
xyz = np.asarray(pc.points)
rgb = np.asarray(pc.colors)

def apply_geo(pts):
    pts = np.asarray(pts)
    s = geo["scale"]
    R = np.array(geo["rotation"])
    t = np.array(geo["translation"])
    origin = np.array(geo["origin"])
    return (pts * s) @ R.T + t - origin

local = apply_geo(xyz)

extent = float(np.linalg.norm(np.ptp(local, axis=0)))
tree = scipy.spatial.cKDTree(local)
nn = tree.query(local, k=2)[0][:, 1]
spacing = max(float(np.median(nn[nn > 0])), extent * 1e-6)

cloud = o3d.geometry.PointCloud()
cloud.points = o3d.utility.Vector3dVector(local)
cloud = cloud.voxel_down_sample(spacing * 0.6)
xyz_down = np.asarray(cloud.points)
cloud.estimate_normals(o3d.geometry.KDTreeSearchParamKNN(knn=min(32, len(xyz_down) - 1)))
normals = np.asarray(cloud.normals)
flip = normals[:, 2] < 0
normals[flip] *= -1
cloud.normals = o3d.utility.Vector3dVector(normals)

surface, density = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
    cloud, depth=9, scale=1.05, linear_fit=False, n_threads=2
)
vertices = np.asarray(surface.vertices)

tree_orig = scipy.spatial.cKDTree(local)
distance, nearest_orig = tree_orig.query(vertices)

local_spacing = tree_orig.query(local, k=6)[0][:, -1]

# Capped at spacing * 15 (Current logic)
tolerance_bug = np.clip(local_spacing[nearest_orig] * 1.8, spacing * 3, spacing * 15)
remove_bug = (distance > tolerance_bug)
s1 = o3d.geometry.TriangleMesh(surface)
s1.remove_vertices_by_mask(remove_bug)
cc1 = s1.cluster_connected_triangles()[1]
print(f"WITH BUG (cap={spacing*15:.3f}m): largest = {np.max(cc1) / max(1, sum(cc1)):.3f}")

# Capped at extent * 0.05 (e.g. 120m * 0.05 = 6m)
tolerance_fix = np.clip(local_spacing[nearest_orig] * 1.8, spacing * 3, extent * 0.05)
remove_fix = (distance > tolerance_fix)
s2 = o3d.geometry.TriangleMesh(surface)
s2.remove_vertices_by_mask(remove_fix)
cc2 = s2.cluster_connected_triangles()[1]
print(f"WITH FIX (cap={extent*0.05:.3f}m): largest = {np.max(cc2) / max(1, sum(cc2)):.3f}")

# What if we just use a larger multiplier? spacing * 50?
tolerance_fix2 = np.clip(local_spacing[nearest_orig] * 1.8, spacing * 3, spacing * 50)
remove_fix2 = (distance > tolerance_fix2)
s3 = o3d.geometry.TriangleMesh(surface)
s3.remove_vertices_by_mask(remove_fix2)
cc3 = s3.cluster_connected_triangles()[1]
print(f"WITH FIX2 (cap={spacing*50:.3f}m): largest = {np.max(cc3) / max(1, sum(cc3)):.3f}")

