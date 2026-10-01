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

depth = 9
mesh_resolution = extent / (2 ** depth)
effective_spacing = max(spacing, mesh_resolution)

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
    cloud, depth=depth, scale=1.05, linear_fit=False, n_threads=2
)
vertices = np.asarray(surface.vertices)

tree_orig = scipy.spatial.cKDTree(local)
distance, nearest_orig = tree_orig.query(vertices)

local_spacing = tree_orig.query(local, k=6)[0][:, -1]
tolerance = np.clip(local_spacing[nearest_orig] * 1.8, effective_spacing * 1.5, effective_spacing * 5)
density = np.asarray(density)
# REMOVE DENSITY FILTER
remove = (distance > tolerance)

surface.remove_vertices_by_mask(remove)
surface.remove_degenerate_triangles()

faces = np.asarray(surface.triangles)
vertices = np.asarray(surface.vertices)

cc = surface.cluster_connected_triangles()[1]
largest_frac = np.max(cc) / max(1, sum(cc)) if len(cc) > 0 else 0
print(f"Largest component: {largest_frac:.3f}")

centroids = vertices[faces].mean(axis=1)
dist_to_cloud, _ = tree_orig.query(centroids)

strong_thresh = max(spacing * 5, mesh_resolution * 1.5)
weak_thresh = max(spacing * 15, mesh_resolution * 3.0)

supported = dist_to_cloud <= strong_thresh
unobserved = dist_to_cloud > weak_thresh
weak = ~(supported | unobserved)

print(f"Supported: {np.mean(supported):.3f}")
print(f"Weak: {np.mean(weak):.3f}")
print(f"Unobserved: {np.mean(unobserved):.3f}")

