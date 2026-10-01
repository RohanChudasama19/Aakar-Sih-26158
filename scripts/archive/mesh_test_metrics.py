import json
import trimesh
import numpy as np
import scipy.spatial
from pathlib import Path
import open3d as o3d

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
ply_10 = work_dir / "dense_10_source_full/fused.ply"

geo = json.loads((work_dir / "alignment.json").read_text())

pc = trimesh.load(str(ply_10))
xyz = np.asarray(pc.vertices)

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

# Load the UNTRIMMED mesh generated earlier or generate it again.
# Wait, I didn't save surf2. Let's just generate it again quickly and measure weak faces!
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
faces = np.asarray(surface.triangles)

centroids = vertices[faces].mean(axis=1)
dist_to_cloud, _ = tree.query(centroids)

strong_thresh = spacing * 5
weak_thresh = spacing * 15

supported = dist_to_cloud <= strong_thresh
unobserved = dist_to_cloud > weak_thresh
weak = ~(supported | unobserved)

print(f"UNTRIMMED MESH:")
print(f"Total faces: {len(faces)}")
print(f"Supported: {np.mean(supported):.3f}")
print(f"Weak: {np.mean(weak):.3f}")
print(f"Unobserved: {np.mean(unobserved):.3f}")

# Now trim ONLY density quantile (unobserved) and re-measure!
density = np.asarray(density)
remove = (density < np.quantile(density, 0.02))
surface.remove_vertices_by_mask(remove)
surface.remove_degenerate_triangles()
vertices = np.asarray(surface.vertices)
faces = np.asarray(surface.triangles)
centroids = vertices[faces].mean(axis=1)
dist_to_cloud, _ = tree.query(centroids)
supported = dist_to_cloud <= strong_thresh
unobserved = dist_to_cloud > weak_thresh
weak = ~(supported | unobserved)

cc2 = surface.cluster_connected_triangles()[1]
print(f"\nTRIMMED ONLY DENSITY (0.02):")
print(f"Largest component: {np.max(cc2) / max(1, sum(cc2)) if len(cc2)>0 else 0}")
print(f"Supported: {np.mean(supported):.3f}")
print(f"Weak: {np.mean(weak):.3f}")
print(f"Unobserved: {np.mean(unobserved):.3f}")

