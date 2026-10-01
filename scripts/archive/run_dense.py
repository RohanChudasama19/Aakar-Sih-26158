import sys, time, json, shutil, subprocess, os
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from app.pipeline.colmap import resolve_colmap_executable, get_colmap_env

work = Path("data/mars_hkairport01_quality/work")
sparse_model = work / "sparse/0"
dense_dir = work / "dense_mars"
dense_dir.mkdir(exist_ok=True, parents=True)

colmap_exe = resolve_colmap_executable()
env = get_colmap_env()

print("PHASE 6: DENSE RECONSTRUCTION")

t0 = time.monotonic()
# 1. Undistort
print("--- Undistorting images ---")
cmd_undistort = [
    colmap_exe, "image_undistorter",
    "--image_path", str(work / "frames"),
    "--input_path", str(sparse_model),
    "--output_path", str(dense_dir),
    "--output_type", "COLMAP",
    "--max_image_size", "1280" # Full res for this dataset
]
subprocess.run(cmd_undistort, capture_output=True, env=env, check=True)
print(f"Undistortion: {time.monotonic()-t0:.1f}s")

# Check undistorted images
images_dir = dense_dir / "images"
image_files = sorted([f.name for f in images_dir.iterdir() if f.is_file()])
print(f"Undistorted images: {len(image_files)}")

# 2. PatchMatch Stereo
t1 = time.monotonic()
print("--- PatchMatch Stereo ---")
stereo_dir = dense_dir / "stereo"
stereo_dir.mkdir(exist_ok=True)

# Build manual patch-match config using all 199 cameras
# to ensure geometric consistency has sources
print("Building patch-match.cfg using manual view selection")
cfg_lines = []
for img in image_files:
    cfg_lines.append(f"{img}")
    cfg_lines.append("__auto__, 10") # Auto select 10 best overlapping views

cfg_path = stereo_dir / "patch-match.cfg"
cfg_path.write_text("\n".join(cfg_lines))

# Run Photometric
cmd_pm_photo = [
    colmap_exe, "patch_match_stereo",
    "--workspace_path", str(dense_dir),
    "--workspace_format", "COLMAP",
    "--PatchMatchStereo.geom_consistency", "0",
    "--PatchMatchStereo.window_radius", "5",
    "--PatchMatchStereo.window_step", "1",
    "--PatchMatchStereo.num_iterations", "5"
]
print("Running Photometric PatchMatch...")
subprocess.run(cmd_pm_photo, capture_output=True, env=env, check=True)

# Run Geometric
cmd_pm_geom = [
    colmap_exe, "patch_match_stereo",
    "--workspace_path", str(dense_dir),
    "--workspace_format", "COLMAP",
    "--PatchMatchStereo.geom_consistency", "1",
    "--PatchMatchStereo.window_radius", "5",
    "--PatchMatchStereo.window_step", "1",
    "--PatchMatchStereo.num_iterations", "5"
]
print("Running Geometric PatchMatch...")
subprocess.run(cmd_pm_geom, capture_output=True, env=env, check=True)
print(f"PatchMatch Stereo: {time.monotonic()-t1:.1f}s")

# Count depth maps
depth_maps = list((stereo_dir / "depth_maps").glob("*.photometric.bin"))
geom_depth_maps = list((stereo_dir / "depth_maps").glob("*.geometric.bin"))
print(f"Photometric depth maps: {len(depth_maps)}")
print(f"Geometric depth maps: {len(geom_depth_maps)}")

# 3. Stereo Fusion
t2 = time.monotonic()
print("--- Stereo Fusion ---")
cmd_fusion = [
    colmap_exe, "stereo_fusion",
    "--workspace_path", str(dense_dir),
    "--workspace_format", "COLMAP",
    "--input_type", "geometric",
    "--output_path", str(dense_dir / "fused.ply"),
    "--StereoFusion.min_num_pixels", "4"
]
subprocess.run(cmd_fusion, capture_output=True, env=env, check=True)
print(f"Stereo Fusion: {time.monotonic()-t2:.1f}s")

print(f"Fused point cloud size: {(dense_dir / 'fused.ply').stat().st_size:,} bytes")
