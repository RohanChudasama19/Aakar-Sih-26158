import os
import subprocess
from pathlib import Path
import shutil
import time

env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
colmap_exe = r"C:\Tools\COLMAP\bin\colmap.exe"
work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
dense_dir = work_dir / "dense_full_ref2"
orig_dense = work_dir / "dense_fast_quality"

shutil.copyfile(str(orig_dense / "stereo/fusion.cfg"), str(dense_dir / "stereo/fusion.cfg"))

print("Running stereo_fusion...")
subprocess.run([
    colmap_exe, "stereo_fusion",
    "--workspace_path", str(dense_dir),
    "--workspace_format", "COLMAP",
    "--input_type", "geometric",
    "--output_path", str(dense_dir / "fused.ply"),
    "--StereoFusion.min_num_pixels", "4",
], check=True, env=env)

import trimesh
pc = trimesh.load(str(dense_dir / "fused.ply"))
print("Fused PLY points:", len(pc.vertices))
