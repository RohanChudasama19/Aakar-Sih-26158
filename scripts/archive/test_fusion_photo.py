import os
import subprocess
from pathlib import Path

env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
colmap_exe = r"C:\Tools\COLMAP\bin\colmap.exe"
dense_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_fast_quality")

cmd_fusion = [
    colmap_exe,
    "stereo_fusion",
    "--workspace_path", str(dense_dir),
    "--workspace_format", "COLMAP",
    "--input_type", "photometric",
    "--output_path", str(dense_dir / "fused_photometric.ply"),
    "--StereoFusion.min_num_pixels", "5",
]
subprocess.run(cmd_fusion, check=True, capture_output=True, text=True, env=env)

import trimesh
pc = trimesh.load(str(dense_dir / "fused_photometric.ply"))
print("Fused PLY points (Photometric):", len(pc.vertices))
