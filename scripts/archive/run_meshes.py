import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))
from app.pipeline.surface import reconstruct_surface
import json
import numpy as np
import open3d as o3d
import time

root = Path("C:/Users/ATHARAV/Documents/sih 26/gpt 6 astra/AAKAR-SIH26158-Surface-Fix/aakar")
work_dir = root / "data/95f51b12-b771-47bf-9201-c3700f9475a7/work"
exp_dir = work_dir / "dense_experiment"

# Load cameras
with open(work_dir / "poses.json", "r") as f:
    poses_dict = json.load(f)

cameras = []
for k, v in poses_dict.items():
    p = np.array(v)
    R = p[:, :3]
    t = p[:, 3]
    # Center is -R^T * t
    c = -R.T @ t
    cameras.append(c)
cameras = np.array(cameras)

def mesh_it(ply_path, name):
    print(f"--- MESHING {name} ---")
    pcd = o3d.io.read_point_cloud(str(ply_path))
    points = np.asarray(pcd.points)
    colors = np.asarray(pcd.colors) * 255.0  # open3d colors are [0,1]
    
    t0 = time.monotonic()
    mesh, report = reconstruct_surface(
        points, 
        colors, 
        cameras, 
        max_points=5000000, 
        options={"mesh_settings": {"depth": 9, "scale": 1.05}}
    )
    print(f"Meshing Runtime: {time.monotonic() - t0:.1f}s")
    print(f"Report: {report}")
    
    o3d.io.write_triangle_mesh(str(exp_dir / f"mesh_{name}.ply"), mesh)
    return report

rep4 = mesh_it(exp_dir / "fused_min4.ply", "min4")
rep2 = mesh_it(exp_dir / "fused_min2.ply", "min2")
