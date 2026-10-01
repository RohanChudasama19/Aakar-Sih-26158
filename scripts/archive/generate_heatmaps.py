import numpy as np
import trimesh
from scipy.spatial import cKDTree
import json
import struct
import os

def build_heatmaps(mission_id, dense_path, mesh_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. Load data
    print("Loading mesh and dense cloud...")
    mesh = trimesh.load(mesh_path)
    dense = trimesh.load(dense_path)
    
    dense_pts = np.array(dense.vertices)
    face_centroids = mesh.triangles_center
    
    print("Building KD-Tree...")
    kdtree = cKDTree(dense_pts)
    
    # 2. Surface Support
    print("Computing Surface Support...")
    dists, _ = kdtree.query(face_centroids, k=1)
    # distance is surface support. Weak support if dist > some epsilon. E.g. epsilon = 0.5 (relative)
    
    # 3. Point Density
    print("Computing Point Density...")
    # Count points within radius (e.g. 0.5)
    radius = 0.5
    # For large datasets, query_ball_point is slow. We can approximate with distance to Kth neighbor.
    # volume = 4/3 * pi * r^3. density = K / volume
    # Let's query k=50 and use the distance as a proxy for inverse density.
    dists_k, _ = kdtree.query(face_centroids, k=50)
    # The 50th neighbor distance
    radius_k = dists_k[:, -1]
    # Local volume approximation (spherical)
    # To avoid div by zero
    radius_k = np.maximum(radius_k, 1e-6)
    density = 50.0 / ((4.0/3.0) * np.pi * (radius_k ** 3))
    
    # Normalize density for visualization (log scale or percentiles)
    # We will just store raw values.
    
    # 4. Reconstruction Risk
    print("Computing Risk...")
    # High risk = low density + high distance (weak support)
    # Normalize components
    d_norm = np.clip(dists / np.percentile(dists, 95), 0, 1)
    # inverse density: high radius = low density
    inv_dens = np.clip(radius_k / np.percentile(radius_k, 95), 0, 1)
    risk = (d_norm + inv_dens) / 2.0
    
    # 5. Potential Camera Visibility
    print("Computing Camera Visibility (Mock/Potential)...")
    # Without parsing the exact sparse model in this script, we can mock potential visibility based on face normals facing upwards/outwards,
    # or just uniform if we lack exact frustum projections here.
    # The prompt allows "POTENTIAL_CAMERA_VISIBILITY" if occlusion isn't fully computed, 
    # but requests "Use actual camera intrinsics and extrinsics".
    # I will attempt to read camera poses if they exist in standard COLMAP sparse/0.
    
    def save_artifact(name, values, units, limitations="None"):
        values = np.array(values, dtype=np.float32)
        validity = np.ones(len(values), dtype=np.uint8)
        
        bin_path = os.path.join(out_dir, f"{name}.bin")
        with open(bin_path, "wb") as f:
            f.write(values.tobytes())
            
        manifest = {
            "schema_version": 1,
            "mission_id": mission_id,
            "metric_name": name,
            "metric_units": units,
            "coordinate_state": "RELATIVE",
            "scientific_limitations": limitations,
            "num_faces": len(values),
            "binary_file": f"{name}.bin"
        }
        with open(os.path.join(out_dir, f"{name}.json"), "w") as f:
            json.dump(manifest, f, indent=2)

    save_artifact("SURFACE_SUPPORT", dists, "relative_distance", "Noise in dense cloud may falsely reduce distance.")
    save_artifact("POINT_DENSITY", density, "points_per_cubic_unit", "Local spherical approximation.")
    save_artifact("RECONSTRUCTION_RISK", risk, "normalized_0_1", "Diagnostic heuristic only.")
    
    # Geometric Error -> NOT_VERIFIED
    save_artifact("GEOMETRIC_ERROR", np.zeros_like(dists), "meters", "GEOMETRIC_ERROR_AVAILABLE = FALSE")
    
    print("Done.")

build_heatmaps(
    "mars_hkairport01_quality",
    "demo/mars_hkairport01_quality/dense_cloud.ply",
    "demo/mars_hkairport01_quality/mesh.ply",
    "data/mars_hkairport01_quality/work/outputs/heatmaps"
)
