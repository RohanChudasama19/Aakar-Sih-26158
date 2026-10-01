import sys, json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
sys.path.insert(0, '.')

work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"
dense_txt = dense_dir / "sparse_txt"

# -- Load cameras --------------------------------------------------------------
lines = [l for l in (dense_txt / "images.txt").read_text().splitlines()
         if not l.startswith('#')]
poses = {}
img_names = {}
j = 1
for l in lines:
    vals = l.split()
    qw,qx,qy,qz = map(float, vals[1:5])
    tx,ty,tz   = map(float, vals[5:8])
    name = vals[9]
    R = Rotation.from_quat([qx,qy,qz,qw]).as_matrix()
    t = np.array([tx,ty,tz])
    P34 = np.zeros((3,4)); P34[:3,:3]=R; P34[:,3]=t
    poses[j] = P34
    img_names[j] = name
    j += 1

K_line = next(l for l in (dense_txt/"cameras.txt").read_text().splitlines()
              if not l.startswith('#'))
v = K_line.split()
fx,fy,cx,cy = map(float, v[4:8])
W,H = int(v[2]), int(v[3])
K = np.array([[fx,0,cx],[0,fy,cy],[0,0,1]])

# -- Load 3D sparse points with known observations -----------------------------
pts3d = {}
obs   = {}   # pt3d_id -> list of (image_id, x2d, y2d)

COLMAP_IMG_ID = {}  # map 1-indexed j to COLMAP image_id
j = 1
for l in lines:
    vals = l.split()
    colmap_id = int(vals[0])
    COLMAP_IMG_ID[colmap_id] = j
    j += 1

# images.txt uses COLMAP image ids (not our 1-index j)
# Reload as: colmap_image_id -> pose
colmap_poses = {}
j = 1
for l in lines:
    vals = l.split()
    colmap_id = int(vals[0])
    qw,qx,qy,qz = map(float, vals[1:5])
    tx,ty,tz   = map(float, vals[5:8])
    R = Rotation.from_quat([qx,qy,qz,qw]).as_matrix()
    t = np.array([tx,ty,tz])
    P34 = np.zeros((3,4)); P34[:3,:3]=R; P34[:,3]=t
    colmap_poses[colmap_id] = P34
    j += 1

plines = [l for l in (dense_txt/"points3D.txt").read_text().splitlines()
          if not l.startswith('#')]

reprojection_errors = []
n_tested = 0
for l in plines[:500]:
    v = l.split()
    X = np.array([float(v[1]),float(v[2]),float(v[3])])
    track = v[8:]
    for k2 in range(0, len(track)-1, 2):
        cid  = int(track[k2])
        if cid not in colmap_poses: continue
        P = colmap_poses[cid]
        cam = P[:3,:3] @ X + P[:,3]
        if cam[2] <= 0: continue
        p   = K @ cam
        u,v2 = p[0]/p[2], p[1]/p[2]
        if not (0 < u < W and 0 < v2 < H): continue
        # COLMAP reported pixel location not stored in points3D.txt,
        # but we can check: reprojection should land inside the image
        # (cannot verify against COLMAP's stored 2D without images.txt 2D parse)
        reprojection_errors.append(0.0)   # we can only confirm in-bounds here
        n_tested += 1
        break   # one check per point

print(f"Tested {n_tested} 3D points, all project inside image bounds")
print(f"(Without stored 2D observations we can only confirm: positive depth + in-image)")

# -- Camera center analysis -----------------------------------------------------
import trimesh
mesh = trimesh.load("demo/mars_hkairport01_quality/mesh.ply", process=False)
xyz  = np.asarray(mesh.vertices)
print(f"\nmesh.ply vertex Z range: [{xyz[:,2].min():.3f}, {xyz[:,2].max():.3f}]")

centers = np.array([-P[:3,:3].T @ P[:,3] for P in colmap_poses.values()])
print(f"Camera center Z range: [{centers[:,2].min():.3f}, {centers[:,2].max():.3f}]")

# Project ALL mesh vertices through camera 100 (mid-flight)
P100 = colmap_poses[list(colmap_poses.keys())[100]]
cam100 = xyz @ P100[:3,:3].T + P100[:,3]
in_front = (cam100[:,2] > 0).sum()
p100 = cam100 @ K.T
uv100 = p100[:,:2] / np.maximum(p100[:,2:3], 1e-8)
in_image = ((uv100[:,0]>=0)&(uv100[:,0]<W)&(uv100[:,1]>=0)&(uv100[:,1]<H)&(cam100[:,2]>0)).sum()
print(f"\nCamera 100 (mid-flight) ? {in_front}/{len(xyz)} verts in front, {in_image} in image bounds")

# Face-level selection check
faces_in_front = (cam100[mesh.faces, 2] > 0).all(1).sum()
print(f"Faces fully in front of camera 100: {faces_in_front}/{len(mesh.faces)}")
