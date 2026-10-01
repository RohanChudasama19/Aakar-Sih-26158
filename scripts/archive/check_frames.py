import sys, json
from pathlib import Path
import numpy as np
import trimesh

sys.path.insert(0, str(Path.cwd()))

work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"
fused_ply = dense_dir / "fused.ply"

# Check point cloud bounds
dense_pc = trimesh.load(str(fused_ply))
pts = np.asarray(dense_pc.vertices)
print(f"Dense cloud bounds:")
print(f"  X: {pts[:,0].min():.3f} to {pts[:,0].max():.3f}")
print(f"  Y: {pts[:,1].min():.3f} to {pts[:,1].max():.3f}")
print(f"  Z: {pts[:,2].min():.3f} to {pts[:,2].max():.3f}")
print(f"  Centroid: {pts.mean(axis=0)}")

# Check camera positions
poses = json.loads((work / "poses.json").read_text())
cameras = []
for p in poses.values():
    m = np.array(p)  # [R|t] 3x4
    R = m[:, :3]
    t = m[:, 3]
    C = -R.T @ t  # world position
    cameras.append(C)
cameras = np.array(cameras)
print(f"\nCamera positions bounds:")
print(f"  X: {cameras[:,0].min():.3f} to {cameras[:,0].max():.3f}")
print(f"  Y: {cameras[:,1].min():.3f} to {cameras[:,1].max():.3f}")
print(f"  Z: {cameras[:,2].min():.3f} to {cameras[:,2].max():.3f}")
print(f"  Centroid: {cameras.mean(axis=0)}")

# Check if cameras are inside/above the point cloud
cloud_z_range = pts[:,2].max() - pts[:,2].min()
cam_z_above = cameras[:,2].mean() - pts[:,2].mean()
print(f"\nCloud Z range: {cloud_z_range:.3f}")
print(f"Camera Z above cloud centroid: {cam_z_above:.3f}")
print(f"This is {'plausible' if 0 < cam_z_above < 1000 else 'WRONG - cameras not above cloud'}")
