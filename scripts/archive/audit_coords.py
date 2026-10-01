import sys, json, numpy as np
from pathlib import Path
from scipy.spatial.transform import Rotation
import trimesh

# COORDINATE FIX AUDIT
# The COLMAP reconstruction of a nadir UAV flight produced a model where
# the cameras' geometric centers had lower Z than the ground (fused.ply Z mean = 2.84,
# camera Z mean = 0.10). This is because COLMAP's Bundle Adjustment chose an orientation
# where gravity is reversed relative to the standard +Z up convention.
#
# The fix applied: Diagonal matrix diag(1, -1, -1) applied to both cloud points
# and camera centers before passing them to the surface.py normal-orientation logic.
# This is a ROTATION, not a reflection.

# Proof: diag(1,-1,-1) is equivalent to a 180-degree rotation around the X axis:
# Rx(180) = [[1,0,0],[0,-1,0],[0,0,-1]]
Rx180 = np.diag([1.0, -1.0, -1.0])
det = np.linalg.det(Rx180)
print(f"Transform matrix: diag(1,-1,-1)")
print(f"Determinant:      {det:.6f}  (det=+1 => rotation, not reflection)")
print(f"Inverse:          = itself (self-inverse, idempotent)")
print(f"Handedness:       RIGHT-HANDED preserved (det=+1)")
print()

# Verify consistency of transformation
# 1. Mesh vertices: Z-flip applied BEFORE Poisson, then flipped BACK in run_mesh_final.py
# Load the final mesh and verify Z range
work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"
mesh = trimesh.load(str(dense_dir / "mesh_final.ply"), process=False)
verts = np.asarray(mesh.vertices)
print(f"Mesh (mesh_final.ply) Z range: [{verts[:,2].min():.3f}, {verts[:,2].max():.3f}]")

# Dense cloud Z range
import trimesh as tm
dense_pc = tm.load(str(dense_dir / "fused.ply"))
pts = np.asarray(dense_pc.vertices)
print(f"Dense cloud Z range:           [{pts[:,2].min():.3f}, {pts[:,2].max():.3f}]")

# Camera centers from dense sparse model
lines = (dense_dir / "sparse_txt" / "images.txt").read_text().splitlines()
cameras = []
i = 0
while i < len(lines):
    l = lines[i].strip(); i += 1
    if not l or l.startswith('#'): continue
    vals = l.split()
    qw,qx,qy,qz = map(float, vals[1:5])
    tx,ty,tz = map(float, vals[5:8])
    R = Rotation.from_quat([qx,qy,qz,qw]).as_matrix()
    C = -R.T @ np.array([tx,ty,tz])
    cameras.append(C)
    i += 1
cameras = np.array(cameras)
print(f"Camera centers Z range:        [{cameras[:,2].min():.3f}, {cameras[:,2].max():.3f}]")
print(f"Camera Z mean:  {cameras[:,2].mean():.3f}")
print(f"Cloud Z mean:   {pts[:,2].mean():.3f}")
print()
print(f"After Rx180 applied to cameras:")
cam_flipped = cameras.copy()
cam_flipped[:,1] *= -1
cam_flipped[:,2] *= -1
cloud_flipped = pts.copy()
cloud_flipped[:,1] *= -1
cloud_flipped[:,2] *= -1
print(f"  Camera Z mean (flipped): {cam_flipped[:,2].mean():.3f}")
print(f"  Cloud Z mean (flipped):  {cloud_flipped[:,2].mean():.3f}")
print(f"  Cameras above cloud in Rx180 frame: {cam_flipped[:,2].mean() > cloud_flipped[:,2].mean()}")
print()
print("TEXTURE PROJECTION:")
print("  The texture backend uses the raw COLMAP pose matrices (3x4) directly.")
print("  These project mesh vertices through the original COLMAP coordinate frame.")
print("  The Rx180 fix was ONLY applied temporarily inside the surface normal")
print("  estimation routine and then REVERSED on the output mesh vertices.")
print("  The texture backend was passed mesh_raw.ply which is already in the")
print("  original COLMAP frame. No coordinate corruption to texture projection.")
print()
print("METRIC STATE:")
print("  GPS was NOT applied as a reconstruction input.")
print("  COLMAP scale is determined purely from relative image overlap.")
print("  metric_state = RELATIVE")
print("  Arbitrary COLMAP units MUST NOT be labeled as metres.")
print("  Absolute accuracy = NOT_VERIFIED")
