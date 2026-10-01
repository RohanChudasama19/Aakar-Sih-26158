import json
import numpy as np
import scipy.spatial
from pathlib import Path
import open3d as o3d
from app.pipeline.georef import transform

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
ply_10 = work_dir / "dense_10_source_full/fused.ply"
geo = json.loads((work_dir / "alignment.json").read_text())
sfm = json.loads((work_dir / "poses.json").read_text())

pc = o3d.io.read_point_cloud(str(ply_10))
xyz = np.asarray(pc.points)
orig_normals = np.asarray(pc.normals)

def apply_geo(pts):
    pts = np.asarray(pts)
    s = geo["scale"]
    R = np.array(geo["rotation"])
    t = np.array(geo["translation"])
    origin = np.array(geo["origin"])
    return (pts * s) @ R.T + t - origin

def apply_geo_normals(norms):
    norms = np.asarray(norms)
    R = np.array(geo["rotation"])
    return norms @ R.T

local = apply_geo(xyz)
local_normals = apply_geo_normals(orig_normals)

extent = float(np.linalg.norm(np.ptp(local, axis=0)))
tree = scipy.spatial.cKDTree(local)
nn = tree.query(local, k=2)[0][:, 1]
spacing = max(float(np.median(nn[nn > 0])), extent * 1e-6)

cloud = o3d.geometry.PointCloud()
cloud.points = o3d.utility.Vector3dVector(local)
cloud.normals = o3d.utility.Vector3dVector(local_normals)

# voxel_down_sample averages the normals!
cloud = cloud.voxel_down_sample(spacing * 0.6)
xyz_down = np.asarray(cloud.points)
normals_down = np.asarray(cloud.normals)
# Normalize the averaged normals
mags = np.linalg.norm(normals_down, axis=1, keepdims=True)
mags[mags == 0] = 1
normals_down /= mags
cloud.normals = o3d.utility.Vector3dVector(normals_down)

# Orient using cameras
cameras = np.array([-np.array(p)[:, :3].T @ np.array(p)[:, 3] for p in sfm.values()])
cameras = apply_geo(cameras)

nearest = scipy.spatial.cKDTree(cameras).query(xyz_down)[1]
flip = np.einsum("ij,ij->i", normals_down, cameras[nearest] - xyz_down) < 0
normals_down[flip] *= -1
cloud.normals = o3d.utility.Vector3dVector(normals_down)

surface, density = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
    cloud, depth=9, scale=1.05, linear_fit=False, n_threads=2
)
vertices = np.asarray(surface.vertices)

tree_orig = scipy.spatial.cKDTree(local)
distance, nearest_orig = tree_orig.query(vertices)
local_spacing = tree_orig.query(local, k=6)[0][:, -1]

tolerance = np.clip(local_spacing[nearest_orig] * 1.8, spacing * 3, spacing * 15)
density = np.asarray(density)
remove = (distance > tolerance) | (density < np.quantile(density, 0.02))

s1 = o3d.geometry.TriangleMesh(surface)
s1.remove_vertices_by_mask(remove)
s1.remove_degenerate_triangles()
cc1 = s1.cluster_connected_triangles()[1]

largest = np.max(cc1) / max(1, sum(cc1)) if len(cc1) > 0 else 0
print(f"WITH ORIGINAL NORMALS (cap={spacing*15:.3f}m): largest = {largest:.3f}")

s2 = o3d.geometry.TriangleMesh(surface)
cc2 = s2.cluster_connected_triangles()[1]
largest2 = np.max(cc2) / max(1, sum(cc2)) if len(cc2) > 0 else 0
print(f"UNTRIMMED WITH ORIGINAL NORMALS: largest = {largest2:.3f}")

