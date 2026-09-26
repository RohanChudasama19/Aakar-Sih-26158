import numpy as np, trimesh
from pathlib import Path
from scipy.spatial.transform import Rotation

work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"
mesh = trimesh.load("demo/mars_hkairport01_quality/mesh.ply", process=False)
xyz = np.asarray(mesh.vertices).copy()
xyz[:, 1] = -xyz[:, 1]
xyz[:, 2] = -xyz[:, 2]
triangles = xyz[mesh.faces]

dense_txt = dense_dir / "sparse_txt"
lines = [l for l in (dense_txt / "images.txt").read_text().splitlines() if not l.startswith('#')]
qw,qx,qy,qz = map(float, lines[0].split()[1:5])
tx,ty,tz = map(float, lines[0].split()[5:8])
R = Rotation.from_quat([qx,qy,qz,qw]).as_matrix()
t = np.array([tx,ty,tz])
K = np.array([[812.27, 0, 629.0], [0, 812.27, 526.0], [0, 0, 1]])

cam = xyz @ R.T + t
p = cam @ K.T
uv = p[:,:2] / np.maximum(p[:,2:3], 1e-8)
triuv = uv[mesh.faces]
area = 0.5 * np.abs(
    triuv[:,0,0] * (triuv[:,1,1] - triuv[:,2,1]) +
    triuv[:,1,0] * (triuv[:,2,1] - triuv[:,0,1]) +
    triuv[:,2,0] * (triuv[:,0,1] - triuv[:,1,1])
)

# only look at faces that are actually in front of this camera
in_front = (cam[mesh.faces, 2] > 0).all(1)
area = area[in_front]

print(f"Valid faces in view: {len(area)}")
if len(area) > 0:
    print(f"Mean triangle area in pixels: {np.mean(area):.2f}")
    print(f"Median triangle area in pixels: {np.median(area):.2f}")
    print(f"Max triangle area in pixels: {np.max(area):.2f}")
    print(f"Faces < 1 pixel area: {(area < 1).sum()} ({(area < 1).sum()/len(area)*100:.1f}%)")
    print(f"Faces < 4 pixel area: {(area < 4).sum()} ({(area < 4).sum()/len(area)*100:.1f}%)")
