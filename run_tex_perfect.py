import sys, json, time
from pathlib import Path
import numpy as np
import trimesh
import cv2
from scipy.spatial.transform import Rotation
sys.path.insert(0, str(Path.cwd()))
from app.pipeline.texture import texture_mesh

work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"

# 1. LOAD EXACT APPROVED MESH (355,173 faces)
mesh = trimesh.load("demo/mars_hkairport01_quality/mesh.ply", process=False)
print(f"Loaded mesh.ply: {len(mesh.faces)} faces")

# 2. LOAD CAMERAS
dense_txt = dense_dir / "sparse_txt"
lines = [l for l in (dense_txt / "images.txt").read_text().splitlines() if not l.startswith('#')]
poses = {}
j_idx = 1
for l in lines:
    vals = l.split()
    qw,qx,qy,qz = map(float, vals[1:5])
    tx,ty,tz = map(float, vals[5:8])
    R = Rotation.from_quat([qx,qy,qz,qw]).as_matrix()
    t = np.array([tx,ty,tz])
    pose_matrix = np.zeros((3, 4))
    pose_matrix[:3, :3] = R
    pose_matrix[:3, 3] = t
    poses[j_idx] = pose_matrix  # INT KEY FIX
    j_idx += 1

clines = [l for l in (dense_txt / "cameras.txt").read_text().splitlines() if not l.startswith('#')]
for l in clines:
    vals = l.split()
    if vals[1] == "PINHOLE":
        fx, fy, cx, cy = map(float, vals[4:8])
        K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]])
        break

# 3. TEXTURE MESH (NO COORDINATE TRANSFORM - MESH IS ALREADY IN COLMAP FRAME)
sfm = {"poses": poses}
geo = {"metric_state": "RELATIVE"}
opts = {"occlusion_test": True, "exposure_normalization": True}

print("Running texture_mesh...")
t1 = time.monotonic()
tex_mesh = texture_mesh(mesh, geo, sfm, K, dense_dir / "tex_images", opts)
print(f"Texture complete in {time.monotonic()-t1:.1f}s")

# 4. EXPORT GLB
glb_out = Path("demo/mars_hkairport01_quality/mesh.glb")
tex_mesh.export(str(glb_out))
print(f"Exported {glb_out.name}: {glb_out.stat().st_size:,} bytes")
