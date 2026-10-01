import sys, json, time, shutil, re
from pathlib import Path
import numpy as np
import trimesh
import cv2

sys.path.insert(0, str(Path.cwd()))
# Custom debug texture function
def debug_texture(mesh, sfm, k, directory):
    xyz = mesh.vertices
    triangles = xyz[mesh.faces]
    centroids = triangles.mean(1)
    
    normal = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    normal_norm = np.linalg.norm(normal, axis=1, keepdims=True) + 1e-12
    normal /= normal_norm

    score = np.zeros(len(triangles))
    selected = np.full(len(triangles), -1, int)
    projections = {}

    for j, pose in sfm["poses"].items():
        image_path = directory / f"{int(j):06d}.png"
        if not image_path.exists():
            print(f"Image {image_path} does not exist!")
            continue
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"Image {image_path} failed to load!")
            continue

        h, w = image.shape[:2]
        cam = xyz @ pose[:, :3].T + pose[:, 3]
        p = cam @ k.T
        uv = p[:, :2] / np.maximum(p[:, 2:3], 1e-8)
        triuv = uv[mesh.faces]

        inside = (
            (triuv[:, :, 0] >= 1)
            & (triuv[:, :, 0] < w - 1)
            & (triuv[:, :, 1] >= 1)
            & (triuv[:, :, 1] < h - 1)
            & (cam[mesh.faces, 2] > 0)
        ).all(1)
        
        view = (-pose[:, :3].T @ pose[:, 3]) - centroids
        distance = np.linalg.norm(view, axis=1)
        angle = np.abs(np.sum(normal * view, axis=1)) / (distance + 1e-9)

        weight = inside * angle / (distance**2 + 1e-9)
        better = weight > score

        selected[better] = j
        score[better] = weight[better]
        projections[j] = uv
        print(f"Cam {j}: inside={inside.sum()} selected={better.sum()}")

    print(f"Total faces: {len(mesh.faces)}, faces selected: {(selected >= 0).sum()}")

    loaded = {}
    for j in sfm["poses"]:
        p = directory / f"{int(j):06d}.png"
        if p.exists():
            loaded[j] = cv2.imread(str(p))
            
    print(f"Loaded {len(loaded)} images.")
    # Verify how many selected faces map to a loaded image
    mapped_count = 0
    for f in range(len(mesh.faces)):
        s = selected[f]
        if s >= 0 and s in loaded and loaded[s] is not None:
            mapped_count += 1
    print(f"Faces that will map to texture: {mapped_count}")

# Prepare data
work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"
mesh = trimesh.load(str(dense_dir / "mesh_raw.ply"), process=False)
tex_img_dir = dense_dir / "tex_images"

from scipy.spatial.transform import Rotation
lines = (dense_dir / "sparse_txt" / "images.txt").read_text().splitlines()
poses = {}
i = 0
j_idx = 1
while i < len(lines):
    l = lines[i].strip(); i += 1
    if not l or l.startswith('#'): continue
    vals = l.split()
    qw,qx,qy,qz = map(float, vals[1:5])
    tx,ty,tz = map(float, vals[5:8])
    R = Rotation.from_quat([qx,qy,qz,qw]).as_matrix()
    t = np.array([tx,ty,tz])
    pose_matrix = np.zeros((3, 4))
    pose_matrix[:3, :3] = R
    pose_matrix[:3, 3] = t
    poses[j_idx] = pose_matrix
    j_idx += 1
    i += 1

K = np.array([[812.27, 0, 629.0], [0, 812.27, 526.0], [0, 0, 1]])
sfm = {"poses": poses}
debug_texture(mesh, sfm, K, tex_img_dir)
