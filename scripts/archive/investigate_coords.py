import sys, json, time
from pathlib import Path
import numpy as np
import trimesh

sys.path.insert(0, str(Path.cwd()))
from app.pipeline.mesh import build_mesh
from app.pipeline.georef import transform

work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"
fused_ply = dense_dir / "fused.ply"

print("Checking fused.ply")
dense_pc = trimesh.load(str(fused_ply))
pts = np.asarray(dense_pc.vertices)
colors = np.asarray(dense_pc.colors)
print(f"Loaded {len(pts)} points")

poses = json.loads((work / "poses.json").read_text())
geo = {"crs": "LOCAL", "offset": [0,0,0], "matrix": np.eye(4).tolist()}
sfm = {"poses": poses}
K = json.loads((work / "intrinsics.json").read_text())["K"]

opts = {
    "profile": "QUALITY",
    "poisson_depth": 9,
    "poisson_scale": 1.05,
    "occlusion_test": True,
    "compute_support": True
}

# Apply the reflection fix correctly inside build_mesh wrapper?
# Actually, the pipeline is supposed to handle COLMAP coordinate systems out of the box.
# Why did it fail initially? Let's check surface.py again. 
# surface.py flips normals based on cameras. If cameras are geometrically below the cloud, it flips normals upwards. 
# If it's a nadir flight, the cameras ARE above the ground in the real world. Why were they below in COLMAP space?
# Because COLMAP reconstruction might have converged upside down relative to the standard Z-up orientation.
# If COLMAP is upside down, we just need to rotate the entire coordinate system by 180 degrees around X or Y, NOT reflect it.
# Reflection changes handedness and breaks projection matrix K!
