import sys, time, json, struct
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

sys.path.insert(0, str(Path.cwd()))
from app.pipeline.colmap import resolve_colmap_executable, get_colmap_env, run as colmap_run

work = Path("data/mars_hkairport01_quality/work")
frames_dir = work / "frames"
sparse_dir = work / "sparse"

colmap_exe = resolve_colmap_executable()
env = get_colmap_env()

print(f"COLMAP exe: {colmap_exe}")
print(f"Frames dir: {frames_dir}, count: {len(list(frames_dir.glob('*.jpg')))}")

# Build camera model -- SIMPLE_PINHOLE estimated for 1280x1070
# f estimated from focal_length = 0.85 * max_dim (reasonable prior for wide UAV)
W, H = 1280, 1070
f_est = 0.85 * max(W, H)
cx, cy = W / 2, H / 2
print(f"Initial intrinsics prior: f={f_est:.1f} cx={cx} cy={cy}")

db = work / "colmap.db"
models = sparse_dir

t0 = time.monotonic()
print()
print("--- Feature extraction ---")

import subprocess
cmd_feat = [
    colmap_exe, "feature_extractor",
    "--database_path", str(db),
    "--image_path", str(frames_dir),
    "--ImageReader.mask_path", str(work / "masks"),
    "--ImageReader.single_camera", "1",
    "--ImageReader.camera_model", "SIMPLE_RADIAL",
    "--ImageReader.camera_params", f"{f_est},{cx},{cy},0.0",
    "--FeatureExtraction.use_gpu", "1",
]
r = subprocess.run(cmd_feat, capture_output=True, text=True, env=env)
if r.returncode != 0:
    print("FEATURE EXTRACTION FAILED:")
    print(r.stderr[-2000:])
    sys.exit(1)
t_feat = time.monotonic() - t0
print(f"Feature extraction: {t_feat:.1f}s")

t1 = time.monotonic()
print("--- Sequential matching ---")
cmd_match = [
    colmap_exe, "sequential_matcher",
    "--database_path", str(db),
    "--SequentialMatching.overlap", "15",
    "--FeatureMatching.use_gpu", "1",
]
r2 = subprocess.run(cmd_match, capture_output=True, text=True, env=env)
if r2.returncode != 0:
    print("MATCHING FAILED:")
    print(r2.stderr[-2000:])
    sys.exit(1)
t_match = time.monotonic() - t1
print(f"Sequential matching: {t_match:.1f}s")

t2 = time.monotonic()
print("--- Mapper (SfM) ---")
cmd_map = [
    colmap_exe, "mapper",
    "--database_path", str(db),
    "--image_path", str(frames_dir),
    "--output_path", str(models),
    "--Mapper.ba_refine_focal_length", "1",
    "--Mapper.ba_refine_principal_point", "0",
    "--Mapper.ba_refine_extra_params", "1",
]
r3 = subprocess.run(cmd_map, capture_output=True, text=True, env=env)
if r3.returncode != 0:
    print("MAPPER FAILED:")
    print(r3.stderr[-2000:])
    sys.exit(1)
t_map = time.monotonic() - t2
t_sfm_total = time.monotonic() - t0
print(f"Mapper: {t_map:.1f}s  |  SfM total: {t_sfm_total:.1f}s")

# Find best model
choices = list(models.glob("*/images.bin"))
if not choices:
    print("ERROR: no sparse model produced")
    sys.exit(1)
model = max(choices, key=lambda p: p.stat().st_size).parent
print(f"Best model: {model}")

# Convert to TXT
textdir = work / "sparse_txt"
textdir.mkdir(exist_ok=True)
cmd_conv = [colmap_exe, "model_converter",
            "--input_path", str(model),
            "--output_path", str(textdir),
            "--output_type", "TXT"]
subprocess.run(cmd_conv, capture_output=True, env=env, check=True)

# Parse cameras registered
images_txt = textdir / "images.txt"
pts_txt = textdir / "points3D.txt"

poses = {}
lines_img = images_txt.read_text().splitlines()
i = 0
while i < len(lines_img):
    l = lines_img[i].strip()
    i += 1
    if not l or l.startswith("#"):
        continue
    vals = l.split()
    name = vals[9]
    qw,qx,qy,qz = map(float, vals[1:5])
    tx,ty,tz = map(float, vals[5:8])
    rot = Rotation.from_quat([qx,qy,qz,qw]).as_matrix()
    poses[name] = np.c_[rot, np.array([tx,ty,tz])]
    i += 1  # skip points2D line

pts_data = [l for l in pts_txt.read_text().splitlines() if l and not l.startswith("#")]
errors_list = [float(l.split()[7]) for l in pts_data]
points3d_count = len(errors_list)
rmse = float(np.sqrt(np.mean(np.square(errors_list)))) if errors_list else 0.0

# Count sparse model sub-components from folders
model_dirs = [d for d in models.iterdir() if d.is_dir() and (d / "images.bin").exists()]

print()
print("=== SPARSE RESULTS ===")
print(f"Selected frames: 200")
print(f"Registered cameras: {len(poses)}")
print(f"Registration ratio: {len(poses)/200*100:.1f}%")
print(f"Sparse 3D points: {points3d_count:,}")
print(f"Reprojection RMSE: {rmse:.3f} px")
print(f"Sub-models found: {len(model_dirs)}")
print(f"SfM runtime: {t_sfm_total:.1f}s")

# Save poses
poses_serial = {k: v.tolist() for k,v in poses.items()}
(work / "poses.json").write_text(json.dumps(poses_serial))

# Save sparse report
sfm_report = {
    "selected_frames": 200,
    "registered_cameras": len(poses),
    "registration_ratio": round(len(poses)/200, 4),
    "sparse_points": points3d_count,
    "reprojection_rmse_px": round(rmse, 4),
    "sub_models": len(model_dirs),
    "best_model_path": str(model),
    "sfm_runtime_s": round(t_sfm_total, 1),
    "feature_extraction_s": round(t_feat, 1),
    "matching_s": round(t_match, 1),
    "mapping_s": round(t_map, 1),
}
(work / "sfm_report.json").write_text(json.dumps(sfm_report, indent=2))
print("sfm_report.json saved")
if len(poses) < 50:
    print("ERROR: fewer than 50 cameras registered -- STOP before dense")
    sys.exit(1)
print("SPARSE GATE: PASS")