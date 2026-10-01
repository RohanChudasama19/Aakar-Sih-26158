import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

sys.path.insert(0, str(Path(".").absolute()))

from app.pipeline.profiles import FAST_QUALITY_V1

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
dense_dir = work_dir / "dense_fast_quality"
stereo_dir = dense_dir / "stereo"

colmap_exe = r"C:\Tools\COLMAP\bin\colmap.exe"
env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}

images_dir = dense_dir / "images"
hidden_dir = dense_dir / "images_hidden"

# Move everything from hidden back to images if previous run left them there
if hidden_dir.exists():
    for f in hidden_dir.iterdir():
        shutil.move(str(f), str(images_dir / f.name))

image_files = sorted([f.name for f in images_dir.iterdir() if f.is_file()])
target_refs = 105
step = len(image_files) / max(1, target_refs) if len(image_files) > target_refs else 1
ref_indices = {int(i * step) for i in range(min(len(image_files), target_refs))}
ref_images = [img for i, img in enumerate(image_files) if i in ref_indices]
non_ref_images = [img for img in image_files if img not in ref_images]

# Delete old geometric depth maps
geom_maps = list((stereo_dir / "depth_maps").glob("*.geometric.bin"))
for f in geom_maps:
    f.unlink()

cfg_lines = []
for img in ref_images:
    cfg_lines.append(f"{img}")
    cfg_lines.append(f"__auto__, 6")
(stereo_dir / "patch-match.cfg").write_text("\n".join(cfg_lines))

print("Hiding non-reference images...")
hidden_dir.mkdir(exist_ok=True)
for img in non_ref_images:
    shutil.move(str(images_dir / img), str(hidden_dir / img))

print("Running Geometric Pass with __auto__...")
cmd_pm_geom = [
    colmap_exe,
    "patch_match_stereo",
    "--workspace_path", str(dense_dir),
    "--workspace_format", "COLMAP",
    "--PatchMatchStereo.max_image_size", "1600",
    "--PatchMatchStereo.geom_consistency", "1",
    "--PatchMatchStereo.window_radius", "4",
    "--PatchMatchStereo.window_step", "2",
    "--PatchMatchStereo.num_iterations", "3",
]
r_pm_geom = subprocess.run(cmd_pm_geom, check=True, capture_output=True, text=True, env=env)

print("Restoring non-reference images...")
for img in non_ref_images:
    shutil.move(str(hidden_dir / img), str(images_dir / img))

print("Running Stereo Fusion...")
cmd_fusion = [
    colmap_exe,
    "stereo_fusion",
    "--workspace_path", str(dense_dir),
    "--workspace_format", "COLMAP",
    "--input_type", "geometric",
    "--output_path", str(dense_dir / "fused2.ply"),
    "--StereoFusion.min_num_pixels", "5",
]
subprocess.run(cmd_fusion, check=True, capture_output=True, text=True, env=env)

import trimesh
pc = trimesh.load(str(dense_dir / "fused2.ply"))
print("Fused PLY points:", len(pc.vertices))
