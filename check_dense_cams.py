# The undistorted COLMAP workspace has its own camera coordinate system.
# We need to read the cameras from the COLMAP dense/sparse model, not from the raw poses.json
# COLMAP's image_undistorter produces a 'sparse' subdirectory with updated positions.
import sys, json
from pathlib import Path
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation

sys.path.insert(0, str(Path.cwd()))
from app.pipeline.colmap import resolve_colmap_executable, get_colmap_env
import subprocess

work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"

# Convert the dense sparse model to TXT format
colmap_exe = resolve_colmap_executable()
env = get_colmap_env()

dense_sparse = dense_dir / "sparse"
dense_txt = dense_dir / "sparse_txt"
dense_txt.mkdir(exist_ok=True)

r = subprocess.run([
    colmap_exe, "model_converter",
    "--input_path", str(dense_sparse),
    "--output_path", str(dense_txt),
    "--output_type", "TXT"
], capture_output=True, env=env)
print(f"model_converter: exit {r.returncode}")
if r.returncode != 0:
    print(r.stderr.decode()[-1000:])

# Now parse the dense cameras
images_txt = dense_txt / "images.txt"
lines = images_txt.read_text().splitlines()
dense_cameras = []
i = 0
while i < len(lines):
    l = lines[i].strip()
    i += 1
    if not l or l.startswith('#'):
        continue
    vals = l.split()
    qw, qx, qy, qz = map(float, vals[1:5])
    tx, ty, tz = map(float, vals[5:8])
    R = Rotation.from_quat([qx, qy, qz, qw]).as_matrix()
    C = -R.T @ np.array([tx, ty, tz])
    dense_cameras.append(C)
    i += 1  # skip 2D points line

dense_cameras = np.array(dense_cameras)
print(f"\nDense camera positions ({len(dense_cameras)} cameras):")
print(f"  X: {dense_cameras[:,0].min():.3f} to {dense_cameras[:,0].max():.3f}")
print(f"  Y: {dense_cameras[:,1].min():.3f} to {dense_cameras[:,1].max():.3f}")
print(f"  Z: {dense_cameras[:,2].min():.3f} to {dense_cameras[:,2].max():.3f}")

# Check dense point cloud
fused_ply = dense_dir / "fused.ply"
dense_pc = trimesh.load(str(fused_ply))
pts = np.asarray(dense_pc.vertices)
print(f"\nDense cloud:")
print(f"  X: {pts[:,0].min():.3f} to {pts[:,0].max():.3f}")
print(f"  Y: {pts[:,1].min():.3f} to {pts[:,1].max():.3f}")
print(f"  Z: {pts[:,2].min():.3f} to {pts[:,2].max():.3f}")

cam_z_above = dense_cameras[:,2].mean() - pts[:,2].mean()
print(f"\nCamera Z above cloud centroid: {cam_z_above:.3f}")
print(f"Status: {'OK - cameras above cloud' if cam_z_above > 0 else 'PROBLEM - cameras below cloud'}")
