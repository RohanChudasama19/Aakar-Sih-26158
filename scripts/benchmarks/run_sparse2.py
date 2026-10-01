import json
import time
import subprocess
from pathlib import Path
from app.schemas import telemetry
from app.pipeline.sfm_backend import execute_sfm
from app.pipeline.georef import align
from app.camera import CameraModelType, CameraModel
import app.pipeline.colmap as colmap_mod

def run_colmap_override(args, work_dir):
    args = [str(a) for a in args]
    print(f"Running: {' '.join(args)}")
    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"FAILED. Return code {e.returncode}")
        raise

colmap_mod.run = run_colmap_override

input_dir = Path("workspace/HKairport01_FAST/inputs")
work = Path("workspace/HKairport01_FAST/work")

gps = telemetry(input_dir / "gps.csv")
frames_dir = input_dir / "images"
info = {"frames": [{"name": p.name} for p in frames_dir.glob("*.jpg")]}

cam = CameraModel(CameraModelType.PINHOLE, 1280, 1071, 600, 600, 640, 535)

def dummy_progress(p, s): pass

print(f"Running SfM on {len(info['frames'])} frames...")
try:
    reconstruction = execute_sfm(frames_dir, info, cam, dummy_progress, force_cpu=False)
    geo = align(reconstruction, gps, input_dir)
    print(f"Registered: {len(reconstruction['poses'])}")
    print(f"Sparse points: {reconstruction['sparse_points']}")
    print(f"RMSE: {geo['rmse']}")
    print(f"Median: {geo['median']}")
    print(f"P95: {geo['p95']}")
except Exception as e:
    print(e)
