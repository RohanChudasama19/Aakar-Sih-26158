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

if dense_dir.exists():
    shutil.rmtree(dense_dir)
dense_dir.mkdir(parents=True)
(dense_dir / "stereo").mkdir(parents=True)
(dense_dir / "stereo" / "depth_maps").mkdir(parents=True)
(dense_dir / "stereo" / "normal_maps").mkdir(parents=True)

# Copy images and sparse
shutil.copytree(orig_dense / "images", dense_dir / "images")
shutil.copytree(orig_dense / "sparse", dense_dir / "sparse")

image_files = sorted([f.name for f in (dense_dir / "images").iterdir() if f.is_file()])
cfg_lines = []
for img in image_files:
    cfg_lines.append(f"{img}")
    cfg_lines.append(f"__auto__, 6")
(dense_dir / "stereo" / "patch-match.cfg").write_text("\n".join(cfg_lines))

print("Running patch_match_stereo (FULL 250)...")
t1 = time.time()
subprocess.run([
    colmap_exe, "patch_match_stereo",
    "--workspace_path", str(dense_dir),
    "--workspace_format", "COLMAP",
    "--PatchMatchStereo.max_image_size", "1600",
    "--PatchMatchStereo.geom_consistency", "1",
    "--PatchMatchStereo.window_radius", "4",
    "--PatchMatchStereo.window_step", "2",
    "--PatchMatchStereo.num_iterations", "3",
], check=True, env=env)
print(f"PatchMatch took {time.time() - t1:.1f}s")

print("Running stereo_fusion...")
t2 = time.time()
subprocess.run([
    colmap_exe, "stereo_fusion",
    "--workspace_path", str(dense_dir),
    "--workspace_format", "COLMAP",
    "--input_type", "geometric",
    "--output_path", str(dense_dir / "fused.ply"),
    "--StereoFusion.min_num_pixels", "4",
], check=True, env=env)
print(f"Fusion took {time.time() - t2:.1f}s")

import trimesh
pc = trimesh.load(str(dense_dir / "fused.ply"))
print("Fused PLY points:", len(pc.vertices))
