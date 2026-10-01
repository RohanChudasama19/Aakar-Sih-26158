import sys, json, time, shutil, re
from pathlib import Path
import numpy as np
import trimesh
import cv2

sys.path.insert(0, str(Path.cwd()))
from app.pipeline.texture import texture_mesh

work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"
mesh = trimesh.load(str(dense_dir / "mesh_raw.ply"), process=False)

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
    poses[str(j_idx)] = pose_matrix
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

fix_mat = np.eye(4)
fix_mat[1, 1] = -1.0
fix_mat[2, 2] = -1.0

geo = {
    "crs": "LOCAL",
    "offset": [0,0,0],
    "matrix": fix_mat.tolist(),
    "metric_state": "RELATIVE"
}
opts = {"occlusion_test": True, "exposure_normalization": True}

print(f"Running texture_mesh with {len(poses)} images...")
t1 = time.monotonic()
try:
    tex_mesh = texture_mesh(mesh, geo, sfm, K, tex_img_dir, opts)
    tex_mesh.export(str(dense_dir / "mesh_textured.glb"))
    print(f"SUCCESS in {time.monotonic()-t1:.1f}s")
except Exception as e:
    import traceback
    traceback.print_exc()
