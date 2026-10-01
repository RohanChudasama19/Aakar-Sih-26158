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
    pose_matrix = np.eye(4)
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
        # Make K a 3x3 matrix. Wait, texture_mesh uses k as 3x3! Let me check the code.
        # Actually texture_mesh takes k and might convert it?
        # In texture.py:
        # def texture_mesh(mesh, geo, sfm, k, directory, options=None):
        # ...
        # If I look at the previous error: "size 3 is different from 4", that implies cam is [N,3] and k.T is [4,4], OR cam is [N,4] and k.T is [3,3].
        # In texture.py: cam = xyz @ pose[:, :3].T + pose[:, 3]. cam is [N,3].
        # So k.T must be [4,4]! Oh, the runner passes k as a 4x4 matrix from intrinsics.json.
        K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]])
        break

# In texture.py: "p = cam @ k.T". So k must be 3x3! Why did it complain?
# Let's print the shapes.
