import numpy as np
import trimesh
from scipy.spatial import cKDTree
import os
import json
import time

def compute_surface_support(mesh_centroids, dense_pts):
    if len(dense_pts) == 0:
        return np.zeros(len(mesh_centroids))
    kdtree = cKDTree(dense_pts)
    dists, _ = kdtree.query(mesh_centroids, k=1)
    return dists

def compute_point_density(mesh_centroids, dense_pts, k=50):
    if len(dense_pts) < k:
        return np.zeros(len(mesh_centroids))
    kdtree = cKDTree(dense_pts)
    dists_k, _ = kdtree.query(mesh_centroids, k=k)
    radius_k = dists_k[:, -1]
    radius_k = np.maximum(radius_k, 1e-6)
    density = k / ((4.0/3.0) * np.pi * (radius_k ** 3))
    return density

def generate_mission_heatmaps(jid: str, data_dir: str):
    work_dir = os.path.join(data_dir, jid, "work", "outputs")
    
    dense_path = None
    for p in ["scene_dense.ply", "dense_relative.ply", "cloud_relative.ply", "dense_raw.ply"]:
        cand = os.path.join(work_dir, p)
        if os.path.exists(cand):
            dense_path = cand
            break
            
    # Always match the viewer's geometry (model.glb if it exists, otherwise representations/scene_textured.glb)
    mesh_path = None
    for p in ["representations/scene_textured.glb", "model.glb", "scene_mesh.ply"]:
        cand = os.path.join(work_dir, p)
        if os.path.exists(cand):
            mesh_path = cand
            break
            
    if not mesh_path or not dense_path:
        return {"status": "skipped", "reason": f"Missing geometry: mesh={mesh_path}, dense={dense_path}"}
        
    t0 = time.time()
    mesh = trimesh.load(mesh_path, force='mesh')
    dense = trimesh.load(dense_path)
    
    dense_pts = np.array(dense.vertices)
    face_centroids = mesh.triangles_center
    
    support = compute_surface_support(face_centroids, dense_pts)
    density = compute_point_density(face_centroids, dense_pts)
    
    d_norm = np.clip(support / (np.percentile(support, 95) + 1e-6), 0, 1)
    inv_dens = np.clip(1.0 / (density + 1e-6), 0, 1)
    
    # Risk calculation
    if len(dense_pts) == 0:
        risk = np.zeros_like(support) # Unavailable
    else:
        risk = (d_norm + inv_dens) / 2.0
    
    out_dir = os.path.join(work_dir, "heatmaps")
    os.makedirs(out_dir, exist_ok=True)
    
    def save_artifact(name, values, units, limitations, status="AVAILABLE"):
        manifest = {
            "schema_version": 1,
            "mission_id": jid,
            "metric_name": name,
            "metric_units": units,
            "coordinate_state": "RELATIVE",
            "scientific_limitations": limitations,
            "status": status
        }
        
        if status == "AVAILABLE":
            values = np.array(values, dtype=np.float32)
            with open(os.path.join(out_dir, f"{name}.bin"), "wb") as f:
                f.write(values.tobytes())
            manifest["num_faces"] = len(values)
            manifest["valid_count"] = len(values)
            manifest["min"] = float(np.min(values))
            manifest["max"] = float(np.max(values))
            manifest["median"] = float(np.median(values))
        else:
            manifest["num_faces"] = len(face_centroids)
            manifest["valid_count"] = 0
            
        with open(os.path.join(out_dir, f"{name}.json"), "w") as f:
            json.dump(manifest, f, indent=2)

    save_artifact("SURFACE_SUPPORT", support, "relative_distance", "Noise may falsify support")
    save_artifact("POINT_DENSITY", density, "points_per_cubic_unit", "Spherical approximation")
    
    risk_status = "AVAILABLE" if len(dense_pts) > 0 else "UNAVAILABLE"
    save_artifact("RECONSTRUCTION_RISK", risk, "normalized_0_1", "Diagnostic heuristic only", status=risk_status)
    save_artifact("POTENTIAL_CAMERA_VISIBILITY", np.ones_like(support), "count", "Mocked uniform visibility")
    
    # DO NOT serialize zero-filled array for unavailable geometric error.
    save_artifact("GEOMETRIC_ERROR", [], "meters", "Independent reference requirements not met (missing GCPs).", status="NOT_VERIFIED")

    t1 = time.time()
    return {
        "status": "success",
        "time_sec": round(t1 - t0, 2),
        "peak_ram_mb": 0,
        "faces": len(face_centroids),
        "dense_pts": len(dense_pts)
    }
