import os
import shutil
import subprocess
import time
from pathlib import Path
import sys

sys.path.append(str(Path.cwd()))
from app.pipeline.colmap import resolve_colmap_executable, get_colmap_env

root = Path("C:/Users/ATHARAV/Documents/sih 26/gpt 6 astra/AeroRecon-SIH26158-Surface-Fix/aerorecon")
work_dir = root / "data/95f51b12-b771-47bf-9201-c3700f9475a7/work"
exp_dir = work_dir / "dense_experiment"

colmap_exe = resolve_colmap_executable() or r"C:\Tools\COLMAP\COLMAP.bat"
env = get_colmap_env()

if exp_dir.exists():
    shutil.rmtree(exp_dir)
exp_dir.mkdir(parents=True)

# 1. Undistort
cmd_undistort = [
    colmap_exe, "image_undistorter",
    "--image_path", str(work_dir / "originals"),
    "--input_path", str(work_dir / "sparse/0"),
    "--output_path", str(exp_dir),
    "--output_type", "COLMAP",
    "--max_image_size", "1600",
]
t0 = time.monotonic()
subprocess.run(cmd_undistort, check=True, env=env)
print(f"Undistort Time: {time.monotonic() - t0:.1f}s")

stereo_dir = exp_dir / "stereo"
stereo_dir.mkdir(exist_ok=True, parents=True)
images_dir = exp_dir / "images"
ref_images = sorted([f.name for f in images_dir.iterdir() if f.is_file()])

cfg_lines_photo = []
for img in ref_images:
    cfg_lines_photo.append(f"{img}")
    cfg_lines_photo.append(f"__auto__, 10")

photo_cfg_path = stereo_dir / "patch-match.cfg"
photo_cfg_path.write_text("\n".join(cfg_lines_photo))

t_pm0 = time.monotonic()
cmd_pm_photo = [
    colmap_exe, "patch_match_stereo",
    "--workspace_path", str(exp_dir),
    "--workspace_format", "COLMAP",
    "--PatchMatchStereo.max_image_size", "1600",
    "--PatchMatchStereo.geom_consistency", "0",
    "--PatchMatchStereo.window_radius", "4",
    "--PatchMatchStereo.window_step", "2",
    "--PatchMatchStereo.num_iterations", "3",
]
subprocess.run(cmd_pm_photo, check=True, env=env)

# Geometric Config
points_map = {}
img_txt = work_dir / "sparse_txt" / "images.txt"
lines = img_txt.read_text().splitlines()
i = 0
while i < len(lines):
    header = lines[i].strip()
    i += 1
    if not header or header.startswith("#"):
        continue
    parts = header.split()
    if len(parts) >= 10:
        name = parts[9]
        pts_line = lines[i].strip()
        i += 1
        pts_parts = pts_line.split()
        pt_ids = {int(pts_parts[j]) for j in range(2, len(pts_parts), 3) if int(pts_parts[j]) != -1}
        points_map[name] = pt_ids

cfg_lines_geom = []
for img in ref_images:
    cfg_lines_geom.append(f"{img}")
    img_pts = points_map.get(img, set())
    overlaps = []
    for other in ref_images:
        if other == img: continue
        shared = len(img_pts.intersection(points_map.get(other, set())))
        overlaps.append((shared, other))
    overlaps.sort(key=lambda x: (x[0], -abs(ref_images.index(img) - ref_images.index(x[1]))), reverse=True)
    best_sources = [x[1] for x in overlaps[:10]]
    cfg_lines_geom.append(", ".join(best_sources))

geom_cfg_path = stereo_dir / "patch-match-geom.cfg"
geom_cfg_path.write_text("\n".join(cfg_lines_geom))
shutil.copyfile(str(geom_cfg_path), str(stereo_dir / "patch-match.cfg"))

cmd_pm_geom = [
    colmap_exe, "patch_match_stereo",
    "--workspace_path", str(exp_dir),
    "--workspace_format", "COLMAP",
    "--PatchMatchStereo.max_image_size", "1600",
    "--PatchMatchStereo.geom_consistency", "1",
    "--PatchMatchStereo.window_radius", "4",
    "--PatchMatchStereo.window_step", "2",
    "--PatchMatchStereo.num_iterations", "3",
]
subprocess.run(cmd_pm_geom, check=True, env=env)
t_pm_end = time.monotonic()
print(f"PatchMatch Time: {t_pm_end - t_pm0:.1f}s")
