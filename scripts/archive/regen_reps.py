import os
import subprocess
from pathlib import Path
import shutil
import time

env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
colmap_exe = r"C:\Tools\COLMAP\bin\colmap.exe"

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
diag_dir = work_dir / "preserved_dense_diagnostics"
diag_dir.mkdir(exist_ok=True)

tmp_dir = work_dir / "tmp_10_source_regen"
if tmp_dir.exists(): shutil.rmtree(tmp_dir)
tmp_dir.mkdir(parents=True)
(tmp_dir / "stereo").mkdir(parents=True)
(tmp_dir / "stereo/depth_maps").mkdir(parents=True)
(tmp_dir / "stereo/normal_maps").mkdir(parents=True)

# Copy images and sparse
shutil.copytree(work_dir / "dense_10_source_full/images", tmp_dir / "images")
shutil.copytree(work_dir / "dense_10_source_full/sparse", tmp_dir / "sparse")

image_files = sorted([f.name for f in (tmp_dir / "images").iterdir() if f.is_file()])
test_images = [image_files[0], image_files[50], image_files[100], image_files[150], image_files[200]]

cfg_lines = []
for img in test_images:
    cfg_lines.append(f"{img}")
    cfg_lines.append(f"__auto__, 10")
(tmp_dir / "stereo/patch-match.cfg").write_text("\n".join(cfg_lines))

print("Regenerating 5 representative maps...")
subprocess.run([
    colmap_exe, "patch_match_stereo",
    "--workspace_path", str(tmp_dir),
    "--workspace_format", "COLMAP",
    "--PatchMatchStereo.max_image_size", "1600",
    "--PatchMatchStereo.geom_consistency", "0",  # photometric only for speed, since we just need representatives
    "--PatchMatchStereo.window_radius", "4",
    "--PatchMatchStereo.window_step", "2",
    "--PatchMatchStereo.num_iterations", "3",
], check=True, env=env)

# Copy to diag_dir
for name in test_images:
    prefix = name
    for ext in [".photometric.bin"]:
        for mtype in ["depth_maps", "normal_maps"]:
            src = tmp_dir / "stereo" / mtype / f"{prefix}{ext}"
            if src.exists():
                shutil.copy2(src, diag_dir / f"{prefix}_{mtype}{ext}")
                print(f"Preserved {src.name}")

shutil.rmtree(tmp_dir)
