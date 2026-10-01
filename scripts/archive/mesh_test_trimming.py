import json
import trimesh
import numpy as np
import scipy.spatial
from pathlib import Path
import open3d as o3d
from app.pipeline.georef import transform

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
ply_10 = work_dir / "dense_10_source_full/fused.ply"

geo = json.loads((work_dir / "alignment.json").read_text())

pc = trimesh.load(str(ply_10))
xyz = np.asarray(pc.vertices)
rgb = np.asarray(pc.colors[:,:3]) if pc.colors is not None else np.zeros_like(xyz)

valid = np.isfinite(xyz).all(axis=1)
xyz, rgb = xyz[valid], rgb[valid]
_, unique = np.unique(np.round(xyz, 8), axis=0, return_index=True)
xyz, rgb = xyz[unique], rgb[unique]

def apply_geo(pts):
    pts = np.asarray(pts)
    s = geo["scale"]
    R = np.array(geo["rotation"])
    t = np.array(geo["translation"])
    origin = np.array(geo["origin"])
    return (pts * s) @ R.T + t - origin

# In pipeline, they use georef.transform.
local = apply_geo(xyz)

extent = float(np.linalg.norm(np.ptp(local, axis=0)))
tree = scipy.spatial.cKDTree(local)
nn = tree.query(local, k=2)[0][:, 1]
spacing = max(float(np.median(nn[nn > 0])), extent * 1e-6)

cloud = o3d.geometry.PointCloud()
cloud.points = o3d.utility.Vector3dVector(local)
cloud.colors = o3d.utility.Vector3dVector(rgb.astype(float) / 255)
cloud = cloud.voxel_down_sample(spacing * 0.6)

xyz_down = np.asarray(cloud.points)
cloud.estimate_normals(o3d.geometry.KDTreeSearchParamKNN(knn=min(32, len(xyz_down) - 1)))

# Let's orient normals using camera positions. Since we don't have camera poses loaded easily, we just use the raw normals for a test meshing.
# Actually Poisson works best with oriented normals.
# We can orient towards Z+ since this is aerial imagery.
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

# Original trimming logic
local_spacing = tree_orig.query(local, k=6)[0][:, -1]
tolerance = np.clip(local_spacing[nearest_orig] * 1.8, spacing * 3, spacing * 15)
density = np.asarray(density)
remove = (distance > tolerance) | (density < np.quantile(density, 0.02))

# Measure largest component WITH removal
surf1 = o3d.geometry.TriangleMesh(surface)
surf1.remove_vertices_by_mask(remove)
surf1.remove_degenerate_triangles()
cc1 = surf1.cluster_connected_triangles()[1]
print(f"WITH TRIMMING: largest = {np.max(cc1) / max(1, sum(cc1)) if len(cc1)>0 else 0}")

# Measure largest component WITHOUT removal
surf2 = o3d.geometry.TriangleMesh(surface)
cc2 = surf2.cluster_connected_triangles()[1]
print(f"WITHOUT TRIMMING: largest = {np.max(cc2) / max(1, sum(cc2)) if len(cc2)>0 else 0}")

