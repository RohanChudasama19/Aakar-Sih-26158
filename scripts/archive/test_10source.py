import os
import subprocess
from pathlib import Path
import shutil
import time

env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
colmap_exe = r"C:\Tools\COLMAP\bin\colmap.exe"
work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
dense_dir = work_dir / "dense_10_source_test"
orig_dense = work_dir / "dense_full_ref2"

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
# Just take first 10 images for the controlled test
test_images = image_files[:10]

cfg_lines = []
for img in test_images:
    cfg_lines.append(f"{img}")
    cfg_lines.append(f"__auto__, 10")
(dense_dir / "stereo" / "patch-match.cfg").write_text("\n".join(cfg_lines))

print("Running patch_match_stereo (10-source test on 10 refs)...")
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

import numpy as np
def read_depth(path):
    with open(path, "rb") as f: data = f.read()
    idx = -1
    for i in range(3): idx = data.find(b"&", idx + 1)
    floats = np.frombuffer(data[idx+1:], dtype=np.float32)
    return floats

geom_maps = list((dense_dir / "stereo/depth_maps").glob("*.geometric.bin"))
valid_fractions = []
for m in geom_maps:
    arr = read_depth(m)
    valid = (arr > 0).sum()
    frac = valid / len(arr)
    valid_fractions.append(frac)

print(f"Tested {len(geom_maps)} maps. Geometric Valid Fractions: {valid_fractions}")
print(f"Median: {np.median(valid_fractions):.3f}")
