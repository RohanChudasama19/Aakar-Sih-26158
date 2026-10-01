import csv
import time
import subprocess
from pathlib import Path
from app.schemas import telemetry
from app.pipeline.sfm_backend import execute_sfm
from app.camera import CameraModelType, CameraModel
from app.pipeline.sensor_fusion import align_trajectories_umeyama
import numpy as np
from scipy.spatial.transform import Rotation
import shutil

# FAST_C: 150 images, 1024 max dim
name = "FAST_C"
print(f"\n--- Running {name} ---")
input_dir = Path(f"workspace/HKairport01_{name}/inputs")
work = Path(f"workspace/HKairport01_{name}/work")
if work.exists(): shutil.rmtree(work)
work.mkdir(parents=True, exist_ok=True)

shutil.copy2("workspace/HKairport01_FAST_baseline/inputs/gps.csv", input_dir / "gps.csv")
shutil.copy2("workspace/HKairport01_FAST_baseline/inputs/flight.json", input_dir / "flight.json")

gps = telemetry(input_dir / "gps.csv")
frames_dir = input_dir / "images"

info = {"frames": [{"name": p.name} for p in frames_dir.glob("*.jpg")]}

with open("data_external/mars_lvig/processed/HKairport01/FAST/frames.csv") as f:
    times = {r["filename"]: float(r["timestamp"]) for r in csv.DictReader(f)}
for fr in info["frames"]:
    fr["time_sec"] = times[fr["name"]]
info["start_time_utc"] = 0.0

scale_factor = 1024 / 2448.0
w = int(2448 * scale_factor)
h = int(2048 * scale_factor)
cam = CameraModel(CameraModelType.PINHOLE, w, h, 600, 600, w//2, h//2)

def dummy_progress(p, s): pass
t0 = time.time()

import app.pipeline.colmap as colmap_mod
orig_run = colmap_mod.run
def run_colmap_override(args, work_dir):
    args = [str(a) for a in args]
    if "feature_extractor" in args:
        args.extend(["--SiftExtraction.max_num_features", "4000"])
    if "sequential_matcher" in args:
        for i, a in enumerate(args):
            if a == "--SequentialMatching.overlap":
                args[i+1] = "15"
    if "mapper" in args:
        pass
    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"FAILED. Return code {e.returncode}")
        raise

colmap_mod.run = run_colmap_override
try:
    execute_sfm(frames_dir, info, cam, dummy_progress, force_cpu=False)
finally:
    colmap_mod.run = orig_run
    
t1 = time.time()
runtime = t1 - t0

textdir = input_dir / "sparse_txt"
poses = {}
lines = (textdir / "images.txt").read_text().splitlines()
i = 0
while i < len(lines):
    line = lines[i].strip()
    i += 1
    if not line or line.startswith("#"): continue
    values = line.split()
    qw, qx, qy, qz = map(float, values[1:5])
    rot = Rotation.from_quat([qx, qy, qz, qw]).as_matrix()
    cname = values[9]
    idx = next((n for n, f in enumerate(info["frames"]) if f["name"] == cname), None)
    if idx is not None:
        poses[idx] = np.c_[rot, np.array(values[5:8], float)]
    i += 1

recon_centers = []
recon_times = []
for idx, fr in enumerate(info["frames"]):
    if idx in poses:
        R = poses[idx][:, :3]
        t = poses[idx][:, 3]
        c = -R.T @ t
        recon_times.append(fr["time_sec"])
        recon_centers.append(c)

recon_centers = np.array(recon_centers)

gt_times_orig = []
gt_centers = []
with open("data_external/mars_lvig/raw/ground_truth/Ground Truth/HKairport01_traj.csv") as f:
    for line in f:
        parts = line.split()
        if not parts: continue
        gt_times_orig.append(float(parts[0]))
        gt_centers.append([float(parts[1]), float(parts[2]), float(parts[3])])

gt_times = np.array(gt_times_orig) + 1671321586.40
gt_centers = np.array(gt_centers)

matched_gt = []
for rt in recon_times:
    closest_idx = np.searchsorted(gt_times, rt)
    if closest_idx == 0: best_idx = 0
    elif closest_idx == len(gt_times): best_idx = len(gt_times) - 1
    else:
        d1 = abs(gt_times[closest_idx] - rt)
        d2 = abs(gt_times[closest_idx-1] - rt)
        best_idx = closest_idx if d1 < d2 else closest_idx - 1
    matched_gt.append(gt_centers[best_idx])

matched_gt = np.array(matched_gt)

try:
    R, t, s = align_trajectories_umeyama(recon_centers, matched_gt, np.ones(len(recon_centers)))
    aligned_recon = s * recon_centers.dot(R.T) + t
    errors = np.linalg.norm(aligned_recon - matched_gt, axis=1)
    rmse = np.sqrt(np.mean(errors**2))
except:
    rmse = -1
    
points = 0
errors_3d = []
with open(textdir / "points3D.txt") as f:
    for line in f:
        if line.startswith("#"): continue
        points += 1
        errors_3d.append(float(line.split()[7]))
        
mean_err = sum(errors_3d)/max(1, len(errors_3d))
coverage = "CONTINUOUS" if len(poses) > len(info["frames"]) * 0.8 else "BROKEN"

print(f"[{name}] SUMMARY:")
print(f"Images: {len(info['frames'])}")
print(f"Registered: {len(poses)}")
print(f"Coverage: {coverage}")
print(f"Points: {points}")
print(f"Reproj Error: {mean_err:.4f}")
print(f"Runtime: {runtime:.1f} s ({runtime/60:.2f} min)")
print(f"Trajectory RMSE: {rmse:.4f} m")
