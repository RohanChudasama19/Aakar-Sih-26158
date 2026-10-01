import sys, json, time, shutil, re
from pathlib import Path
import numpy as np
import trimesh
import cv2

sys.path.insert(0, str(Path.cwd()))
from app.pipeline.texture import texture_mesh

work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"
# LOAD THE ORIGINAL APPROVED GEOMETRY (355,173 faces)
mesh = trimesh.load("demo/mars_hkairport01_quality/mesh.ply", process=False)
print(f"Loaded approved mesh.ply: {len(mesh.faces)} faces")

tex_img_dir = dense_dir / "tex_images"
from scipy.spatial.transform import Rotation
dense_txt = dense_dir / "sparse_txt"
images_txt = dense_txt / "images.txt"
lines = images_txt.read_text().splitlines()
poses = {}
i = 0
j_idx = 1
while i < len(lines):
    l = lines[i].strip(); i += 1
    if not l or l.startswith('#'): continue
    vals = l.split()
    qw,qx,qy,qz = map(float, vals[1:5])
    tx,ty,tz = map(float, vals[5:8])
    name = vals[9]
    R = Rotation.from_quat([qx,qy,qz,qw]).as_matrix()
    t = np.array([tx,ty,tz])
    pose_matrix = np.zeros((3, 4))
    pose_matrix[:3, :3] = R
    pose_matrix[:3, 3] = t
    
    # CRUCIAL FIX: use INTEGER keys so texture.py doesn't silently fail
    poses[j_idx] = pose_matrix
    j_idx += 1
    i += 1

cams_txt = dense_txt / "cameras.txt"
clines = cams_txt.read_text().splitlines()
for l in clines:
    if l.startswith('#'): continue
    vals = l.split()
    if vals[1] == "PINHOLE":
        fx, fy, cx, cy = map(float, vals[4:8])
        K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]])
        break

sfm = {"poses": poses}

# CRITICAL GEOMETRY MATCHING:
# mesh.ply is already correctly oriented (it has the Rx180 fix applied directly to its vertices).
# The cameras in poses are in the ORIGINAL COLMAP frame.
# We must temporarily rotate the mesh BACK to the COLMAP frame before passing it to texture_mesh.
xyz = np.asarray(mesh.vertices).copy()
xyz[:, 1] = -xyz[:, 1]
xyz[:, 2] = -xyz[:, 2]
mesh.vertices = xyz

# Now mesh and cameras are both in COLMAP frame.
# We can texture project.
geo = {"metric_state": "RELATIVE"}
opts = {"occlusion_test": True, "exposure_normalization": True}

print(f"Running texture_mesh with {len(poses)} images (INT keys)...")
t1 = time.monotonic()
tex_mesh = texture_mesh(mesh, geo, sfm, K, tex_img_dir, opts)

# The returned tex_mesh is in the COLMAP frame. We must rotate it back to the saved (Rx180) frame!
xyz_tex = np.asarray(tex_mesh.vertices).copy()
xyz_tex[:, 1] = -xyz_tex[:, 1]
xyz_tex[:, 2] = -xyz_tex[:, 2]
tex_mesh.vertices = xyz_tex

tex_mesh.export("demo/mars_hkairport01_quality/mesh.glb")
print(f"SUCCESS in {time.monotonic()-t1:.1f}s")
