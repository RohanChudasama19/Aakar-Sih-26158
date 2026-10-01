import json
import trimesh
import numpy as np
import scipy.spatial
from pathlib import Path
import open3d as o3d

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
ply_6 = work_dir / "dense_full_ref2/fused.ply"
mesh_6 = work_dir / "dense_full_ref2/mesh_raw.ply"
ply_10 = work_dir / "dense_10_source_full/fused.ply"
mesh_10 = work_dir / "dense_10_source_full/mesh_raw.ply"

results = {}

def analyze_mesh(mesh_path, ply_path):
    print(f"Analyzing {mesh_path.name} ...")
    mesh = trimesh.load(str(mesh_path))
    pc = trimesh.load(str(ply_path))
    
    verts = mesh.vertices
    faces = mesh.faces
    
    # 1. Independent components using Open3D
    o3d_mesh = o3d.geometry.TriangleMesh()
    o3d_mesh.vertices = o3d.utility.Vector3dVector(verts)
    o3d_mesh.triangles = o3d.utility.Vector3iVector(faces)
    
    triangle_clusters, cluster_n_triangles, cluster_area = o3d_mesh.cluster_connected_triangles()
    triangle_clusters = np.asarray(triangle_clusters)
    cluster_n_triangles = np.asarray(cluster_n_triangles)
    cluster_area = np.asarray(cluster_area)
    
    if len(cluster_n_triangles) > 0:
        largest_comp = cluster_n_triangles.max()
        largest_frac = largest_comp / max(1, len(faces))
    else:
        largest_comp = 0
        largest_frac = 0
        
    invalid_faces = np.sum((faces < 0) | (faces >= len(verts)))
    
    # Calculate triangle areas
    v0 = verts[faces[:, 0]]
    v1 = verts[faces[:, 1]]
    v2 = verts[faces[:, 2]]
    area_faces = 0.5 * np.linalg.norm(np.cross(v1 - v0, v2 - v0), axis=1)
    degen_faces = np.sum(area_faces < 1e-10)
    
    isolated_verts = len(verts) - len(np.unique(faces))
    
    # Dense cloud validity
    valid_points = np.isfinite(pc.vertices).all(axis=1)
    pts = pc.vertices[valid_points]
    bbox_min, bbox_max = pts.min(axis=0), pts.max(axis=0)
    
    # Weak faces logic independent implementation
    centroids = verts[faces].mean(axis=1)
    tree = scipy.spatial.cKDTree(pts)
    dist_to_cloud, _ = tree.query(centroids)
    
    nn = tree.query(pts, k=2)[0][:, 1]
    extent = float(np.linalg.norm(bbox_max - bbox_min))
    spacing = max(float(np.median(nn[nn > 0])), extent * 1e-6)
    
    strong_thresh = spacing * 5
    weak_thresh = spacing * 15
    supported = dist_to_cloud <= strong_thresh
    unobserved = dist_to_cloud > weak_thresh
    weak = ~(supported | unobserved)
    
    return {
        "verts": len(verts),
        "faces": len(faces),
        "components": len(cluster_n_triangles),
        "largest_face_count": largest_comp,
        "largest_frac": largest_frac,
        "invalid_faces": int(invalid_faces),
        "degen_faces": int(degen_faces),
        "isolated_verts": int(isolated_verts),
        "dense_points": len(pts),
        "weak_frac": float(np.mean(weak)),
        "supported_frac": float(np.mean(supported)),
        "spacing": spacing
    }

print("Results for 6-source:")
res_6 = analyze_mesh(mesh_6, ply_6)
for k, v in res_6.items(): print(f"  {k}: {v}")

print("Results for 10-source:")
res_10 = analyze_mesh(mesh_10, ply_10)
for k, v in res_10.items(): print(f"  {k}: {v}")
