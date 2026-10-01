import sys, json, cv2, numpy as np
from pathlib import Path
from scipy.spatial.transform import Rotation

sys.path.insert(0, str(Path.cwd()))

work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"
dense_txt = dense_dir / "sparse_txt"

# Load cameras from sparse model
lines = (dense_txt / "images.txt").read_text().splitlines()
cams = {}
i = 0
while i < len(lines):
    l = lines[i].strip(); i += 1
    if not l or l.startswith('#'): continue
    vals = l.split()
    name = vals[9]
    qw,qx,qy,qz = map(float, vals[1:5])
    tx,ty,tz = map(float, vals[5:8])
    R = Rotation.from_quat([qx,qy,qz,qw]).as_matrix()
    t = np.array([tx,ty,tz])
    P34 = np.zeros((3,4)); P34[:3,:3]=R; P34[:,3]=t
    cams[name] = P34
    i += 1

# Load K from PINHOLE cameras.txt
for l in (dense_txt / "cameras.txt").read_text().splitlines():
    if l.startswith('#'): continue
    v = l.split()
    if v[1] == "PINHOLE":
        fx,fy,cx,cy = map(float, v[4:8])
        K = np.array([[fx,0,cx],[0,fy,cy],[0,0,1]])
        W,H = int(v[2]), int(v[3])
        break
print(f"K={K.tolist()}  W={W} H={H}")

# Load COLMAP sparse 3D points with known observations
pts_lines = (dense_txt / "points3D.txt").read_text().splitlines()
print(f"Loaded {len(pts_lines)} sparse points")

# Test reprojection on a sample of points
errors = []
for l in pts_lines[:1000]:
    if not l or l.startswith('#'): continue
    v = l.split()
    X = np.array([float(v[1]),float(v[2]),float(v[3])])
    # track = pairs of (img_id, pt2d_id) from v[8:]
    track = v[8:]
    for k2 in range(0, len(track)-1, 2):
        img_id = int(track[k2])
        # find cam name with this img_id (we need to look it up)
        # Actually track stores image_id and point2d_idx
        # We need to find which camera has this image_id
        # Let's just use known camera names
        pass

# Simpler: pick the first camera, project its known sparse points
cam_names = list(cams.keys())[:3]
print(f"\nTesting cameras: {cam_names}")
for name in cam_names:
    P = cams[name]
    # Project 5 test world points through this camera
    # Use the COLMAP point cloud bounds as test points
    import trimesh
    dense_pc = trimesh.load(str(dense_dir / "fused.ply"))
    pts3d = np.asarray(dense_pc.vertices)[:5]
    
    cam_coords = pts3d @ P[:3,:3].T + P[:,3]
    in_front = (cam_coords[:,2] > 0).sum()
    p = cam_coords @ K.T
    uv = p[:,:2] / p[:,2:3]
    in_image = ((uv[:,0]>=0)&(uv[:,0]<W)&(uv[:,1]>=0)&(uv[:,1]<H)).sum()
    print(f"  {name}: cam_coords Z range [{cam_coords[:,2].min():.3f},{cam_coords[:,2].max():.3f}] in_front={in_front}/5 in_image={in_image}/5")
    print(f"    UV sample: {np.round(uv,1).tolist()}")
