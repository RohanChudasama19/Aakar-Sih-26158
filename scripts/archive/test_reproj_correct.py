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
poses_colmap = {}
img_names = {}
points2d_per_image = {}  # colmap_id -> (x2d, y2d, pt3d_id)

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
    # parse pts2d line
    pts_line = raw[i+1].split()
    pts2d = []
    for k2 in range(0, len(pts_line)-2, 3):
        x2d = float(pts_line[k2]); y2d = float(pts_line[k2+1]); pt3d_id = int(pts_line[k2+2])
        if pt3d_id >= 0:
            pts2d.append((x2d, y2d, pt3d_id))
    points2d_per_image[cid] = pts2d
    i += 2

K_line = next(l for l in (dense_txt/"cameras.txt").read_text().splitlines() if not l.startswith('#'))
v = K_line.split(); fx,fy,cx,cy = map(float, v[4:8]); W,H = int(v[2]),int(v[3])
K = np.array([[fx,0,cx],[0,fy,cy],[0,0,1]])

# Load 3D points
pts3d_dict = {}
for l in (dense_txt/"points3D.txt").read_text().splitlines():
    if l.startswith('#'): continue
    v = l.split()
    pts3d_dict[int(v[0])] = np.array([float(v[1]),float(v[2]),float(v[3])])

# -- Reprojection test using actual COLMAP observations -------------------------
cids = list(poses_colmap.keys())[:5]
all_errors = []
for cid in cids:
    P = poses_colmap[cid]
    pts2d = points2d_per_image.get(cid, [])[:50]
    errors = []
    for x2d, y2d, pt3d_id in pts2d:
        if pt3d_id not in pts3d_dict: continue
        X = pts3d_dict[pt3d_id]
        cam = P[:3,:3] @ X + P[:,3]
        if cam[2] <= 0: continue
        p = K @ cam
        u = p[0]/p[2]; v2 = p[1]/p[2]
        err = np.sqrt((u-x2d)**2 + (v2-y2d)**2)
        errors.append(err)
    if errors:
        print(f"Camera {cid} ({img_names[cid]}): {len(errors)} obs, mean reproj err = {np.mean(errors):.4f} px")
        all_errors.extend(errors)

print(f"\nOverall: {len(all_errors)} observations, mean = {np.mean(all_errors):.4f} px, max = {np.max(all_errors):.4f} px")
print(f"All below 2px: {all([e < 2 for e in all_errors])}")
print(f"% below 1px: {sum(e < 1 for e in all_errors)/len(all_errors)*100:.1f}%")
