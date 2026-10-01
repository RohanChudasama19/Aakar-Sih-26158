import os
import subprocess
from pathlib import Path
import trimesh

env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
colmap_exe = r"C:\Tools\COLMAP\bin\colmap.exe"
dense_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_fast_quality")

def run_fusion(inputType, min_pixels, outname):
    outpath = dense_dir / outname
    cmd = [
        colmap_exe, "stereo_fusion",
        "--workspace_path", str(dense_dir),
        "--workspace_format", "COLMAP",
        "--input_type", inputType,
        "--output_path", str(outpath),
        "--StereoFusion.min_num_pixels", str(min_pixels),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    pc = trimesh.load(str(outpath))
    print(f"{inputType} min{min_pixels}: {len(pc.vertices)} points")

run_fusion("photometric", 4, "fused_photo_4.ply")
run_fusion("geometric", 4, "fused_geom_4.ply")
run_fusion("geometric", 3, "fused_geom_3.ply")
run_fusion("geometric", 2, "fused_geom_2.ply")
