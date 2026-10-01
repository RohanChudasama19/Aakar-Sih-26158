import os
import sys
import shutil
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(".").absolute()))

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
dense_dir = work_dir / "dense_fast_quality"
stereo_dir = dense_dir / "stereo"

colmap_exe = r"C:\Tools\COLMAP\bin\colmap.exe"
env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}

images_dir = dense_dir / "images"
hidden_dir = dense_dir / "images_hidden"

if hidden_dir.exists():
    for f in hidden_dir.iterdir():
        shutil.move(str(f), str(images_dir / f.name))

if (dense_dir / "sparse_full").exists():
    shutil.rmtree(dense_dir / "sparse")
    shutil.move(str(dense_dir / "sparse_full"), str(dense_dir / "sparse"))

image_files = sorted([f.name for f in images_dir.iterdir() if f.is_file()])
target_refs = 105
step = len(image_files) / max(1, target_refs) if len(image_files) > target_refs else 1
ref_indices = {int(i * step) for i in range(min(len(image_files), target_refs))}
ref_images = [img for i, img in enumerate(image_files) if i in ref_indices]
non_ref_images = [img for img in image_files if img not in ref_images]

geom_maps = list((stereo_dir / "depth_maps").glob("*.geometric.bin"))
for f in geom_maps:
    f.unlink()

shutil.move(str(dense_dir / "sparse"), str(dense_dir / "sparse_full"))
(dense_dir / "sparse").mkdir()
del_list = dense_dir / "del_list.txt"
del_list.write_text("\n".join(non_ref_images))

subprocess.run([
    colmap_exe, "image_deleter",
    "--input_path", str(dense_dir / "sparse_full"),
    "--output_path", str(dense_dir / "sparse"),
    "--image_names_path", str(del_list)
], check=True, env=env)

# Hide images
hidden_dir.mkdir(exist_ok=True)
for img in non_ref_images:
    shutil.move(str(images_dir / img), str(hidden_dir / img))

cfg_lines = []
for img in ref_images:
    cfg_lines.append(f"{img}")
    cfg_lines.append(f"__auto__, 6")
(stereo_dir / "patch-match.cfg").write_text("\n".join(cfg_lines))

print("Running Geometric Pass with __auto__ + hidden images + deleted sparse...")
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
r_pm_geom = subprocess.run(cmd_pm_geom, capture_output=True, text=True, env=env)
print("Return code:", r_pm_geom.returncode)

# Restore
for img in non_ref_images:
    shutil.move(str(hidden_dir / img), str(images_dir / img))
shutil.rmtree(dense_dir / "sparse")
shutil.move(str(dense_dir / "sparse_full"), str(dense_dir / "sparse"))

if r_pm_geom.returncode == 0:
    subprocess.run([
        colmap_exe, "stereo_fusion",
        "--workspace_path", str(dense_dir),
        "--workspace_format", "COLMAP",
        "--input_type", "geometric",
        "--output_path", str(dense_dir / "fused_deleter2.ply"),
        "--StereoFusion.min_num_pixels", "5",
    ], check=True, env=env)
    import trimesh
    pc = trimesh.load(str(dense_dir / "fused_deleter2.ply"))
    print("Fused PLY points:", len(pc.vertices))
else:
    print("FAILED")
