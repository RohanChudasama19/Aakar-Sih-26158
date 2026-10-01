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

cloud = o3d.geometry.PointCloud()
cloud.points = o3d.utility.Vector3dVector(local)
cloud = cloud.voxel_down_sample(spacing * 0.6)
xyz_down = np.asarray(cloud.points)
cloud.estimate_normals(o3d.geometry.KDTreeSearchParamKNN(knn=min(32, len(xyz_down) - 1)))

surface, density = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
    cloud, depth=9, scale=1.05, linear_fit=False, n_threads=2
)
vertices = np.asarray(surface.vertices)

tree_orig = scipy.spatial.cKDTree(local)
distance, nearest_orig = tree_orig.query(vertices)
local_spacing = tree_orig.query(local, k=6)[0][:, -1]

# Current logic
tolerance = np.clip(local_spacing[nearest_orig] * 1.8, spacing * 3, spacing * 15)
density = np.asarray(density)
remove_dist_and_dens = (distance > tolerance) | (density < np.quantile(density, 0.02))
remove_dist_only = (distance > tolerance)
remove_dens_only = (density < np.quantile(density, 0.02))

s1 = o3d.geometry.TriangleMesh(surface)
s1.remove_vertices_by_mask(remove_dist_and_dens)
cc1 = s1.cluster_connected_triangles()[1]
print(f"Dist + Dens: {np.max(cc1) / max(1, sum(cc1)) if len(cc1)>0 else 0:.3f}")

s2 = o3d.geometry.TriangleMesh(surface)
s2.remove_vertices_by_mask(remove_dist_only)
cc2 = s2.cluster_connected_triangles()[1]
print(f"Dist only: {np.max(cc2) / max(1, sum(cc2)) if len(cc2)>0 else 0:.3f}")

s3 = o3d.geometry.TriangleMesh(surface)
s3.remove_vertices_by_mask(remove_dens_only)
cc3 = s3.cluster_connected_triangles()[1]
print(f"Dens only: {np.max(cc3) / max(1, sum(cc3)) if len(cc3)>0 else 0:.3f}")

