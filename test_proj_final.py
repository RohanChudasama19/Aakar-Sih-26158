import sys, json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
sys.path.insert(0,'.')

work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"
dense_txt = dense_dir / "sparse_txt"

# Parse images.txt correctly (every TWO non-comment lines = one image)
raw = [l for l in (dense_txt/"images.txt").read_text().splitlines() if not l.startswith('#')]
poses_colmap = {}   # colmap_image_id -> 3x4 P
img_names = {}

i = 0
while i < len(raw):
    vals = raw[i].split()
    cid = int(vals[0])
    qw,qx,qy,qz = map(float, vals[1:5])
    tx,ty,tz     = map(float, vals[5:8])
    name         = vals[9]
    R = Rotation.from_quat([qx,qy,qz,qw]).as_matrix()
    t = np.array([tx,ty,tz])
    P = np.zeros((3,4)); P[:3,:3]=R; P[:,3]=t
    poses_colmap[cid] = P
    img_names[cid] = name
    i += 2   # skip the POINTS2D line

K_line = next(l for l in (dense_txt/"cameras.txt").read_text().splitlines() if not l.startswith('#'))
v = K_line.split(); fx,fy,cx,cy = map(float, v[4:8]); W,H = int(v[2]),int(v[3])
K = np.array([[fx,0,cx],[0,fy,cy],[0,0,1]])
print(f"K = {K.tolist()}  W={W} H={H}")
print(f"Loaded {len(poses_colmap)} cameras")

# -- Load 3D sparse points -----------------------------------------------------
plines = [l for l in (dense_txt/"points3D.txt").read_text().splitlines() if not l.startswith('#')]
print(f"Sparse 3D points: {len(plines)}")

# -- Reprojection test on a subset --------------------------------------------
errs = []
tested = 0
for l in plines[:300]:
    v = l.split()
    X = np.array([float(v[1]),float(v[2]),float(v[3])])
    track = v[8:]
    for k2 in range(0, len(track)-3, 3):
        cid = int(track[k2])
        x2d = float(track[k2+1])
        y2d = float(track[k2+2])
        if cid not in poses_colmap: continue
        P = poses_colmap[cid]
        cam = P[:3,:3] @ X + P[:,3]
        if cam[2] <= 0: continue
        p = K @ cam
        u = p[0]/p[2]; v_proj = p[1]/p[2]
        err = np.sqrt((u-x2d)**2 + (v_proj-y2d)**2)
        errs.append(err)
        tested += 1
        break

if errs:
    print(f"Reprojection test: {tested} points, mean error = {np.mean(errs):.4f} px, max = {np.max(errs):.4f} px")
    print(f"  All below 2px: {(np.array(errs) < 2).all()}")

# -- mesh.ply projection health -------------------------------------------------
import trimesh
mesh = trimesh.load("demo/mars_hkairport01_quality/mesh.ply", process=False)
xyz = np.asarray(mesh.vertices)
print(f"\nmesh.ply: {len(mesh.faces)} faces, Z range [{xyz[:,2].min():.3f}, {xyz[:,2].max():.3f}]")

# Camera 110 (mid-flight by COLMAP id)
cids = sorted(poses_colmap.keys())
mid_cid = cids[110]
P = poses_colmap[mid_cid]
cam = xyz @ P[:3,:3].T + P[:,3]
in_front = (cam[:,2] > 0).sum()
p = cam @ K.T
uv = p[:,:2] / np.maximum(p[:,2:3], 1e-8)
in_image = ((uv[:,0]>=0)&(uv[:,0]<W)&(uv[:,1]>=0)&(uv[:,1]<H)&(cam[:,2]>0)).sum()
print(f"Camera {mid_cid}: {in_front}/{len(xyz)} verts in front, {in_image} in image bounds")

# Face selection
triZ = cam[mesh.faces, 2]
faces_fully_in_front = (triZ > 0).all(1).sum()
print(f"Faces fully in front of camera {mid_cid}: {faces_fully_in_front}/{len(mesh.faces)}")

# -- tex_images availability -----------------------------------------------------
tex_dir = dense_dir / "tex_images"
png_files = list(tex_dir.glob("*.png"))
print(f"\nTex images available: {len(png_files)}")
print(f"  Range: {sorted(png_files)[0].name} -> {sorted(png_files)[-1].name}")
