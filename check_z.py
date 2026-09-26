import numpy as np, trimesh
from scipy.spatial.transform import Rotation
from pathlib import Path

mesh = trimesh.load("demo/mars_hkairport01_quality/mesh.ply", process=False)
xyz = np.asarray(mesh.vertices).copy()

dense_txt = Path("data/mars_hkairport01_quality/work/dense_mars/sparse_txt")
lines = [l for l in (dense_txt / "images.txt").read_text().splitlines() if not l.startswith('#')]
qw,qx,qy,qz = map(float, lines[0].split()[1:5])
tx,ty,tz = map(float, lines[0].split()[5:8])
R = Rotation.from_quat([qx,qy,qz,qw]).as_matrix()
t = np.array([tx,ty,tz])

# What if we DON'T transform xyz?
cam1 = xyz @ R.T + t
print("cam1 Z range (untransformed):", cam1[:,2].min(), cam1[:,2].max())

# What if we DO transform xyz?
xyz2 = xyz.copy()
xyz2[:, 1] = -xyz2[:, 1]
xyz2[:, 2] = -xyz2[:, 2]
cam2 = xyz2 @ R.T + t
print("cam2 Z range (transformed):", cam2[:,2].min(), cam2[:,2].max())
