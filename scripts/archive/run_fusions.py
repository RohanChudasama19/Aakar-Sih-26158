import os
import subprocess
import time
from pathlib import Path
import sys

sys.path.append(str(Path.cwd()))
from app.pipeline.colmap import resolve_colmap_executable, get_colmap_env
from app.pipeline.mesh import build_mesh

root = Path("C:/Users/ATHARAV/Documents/sih 26/gpt 6 astra/AAKAR-SIH26158-Surface-Fix/aakar")
work_dir = root / "data/95f51b12-b771-47bf-9201-c3700f9475a7/work"
exp_dir = work_dir / "dense_experiment"
colmap_exe = resolve_colmap_executable() or r"C:\Tools\COLMAP\COLMAP.bat"
env = get_colmap_env()

def run_fusion(min_pixels, out_ply):
    print(f"--- FUSION min_num_pixels={min_pixels} ---")
    t0 = time.monotonic()
    cmd = [
        colmap_exe, "stereo_fusion",
        "--workspace_path", str(exp_dir),
        "--workspace_format", "COLMAP",
        "--input_type", "geometric",
        "--output_path", str(out_ply),
        "--StereoFusion.min_num_pixels", str(min_pixels)
    ]
    subprocess.run(cmd, check=True, env=env)
    print(f"Fusion {min_pixels} Runtime: {time.monotonic() - t0:.1f}s")
    
    import open3d as o3d
    pcd = o3d.io.read_point_cloud(str(out_ply))
    print(f"Fused points (min={min_pixels}): {len(pcd.points)}")
    return out_ply

# Run Fusion Min=4
ply4 = exp_dir / "fused_min4.ply"
run_fusion(4, ply4)

# Run Fusion Min=2
ply2 = exp_dir / "fused_min2.ply"
run_fusion(2, ply2)

# Run Meshing
mesh_settings = {"depth": 9, "scale": 1.05}

print("--- MESHING MIN 4 ---")
t0 = time.monotonic()
res4 = build_mesh(str(ply4), str(exp_dir / "mesh_min4.ply"), mesh_settings)
print(f"Mesh4 Runtime: {time.monotonic() - t0:.1f}s")
print(res4)

print("--- MESHING MIN 2 ---")
t0 = time.monotonic()
res2 = build_mesh(str(ply2), str(exp_dir / "mesh_min2.ply"), mesh_settings)
print(f"Mesh2 Runtime: {time.monotonic() - t0:.1f}s")
print(res2)
