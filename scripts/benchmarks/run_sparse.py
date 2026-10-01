import json
import time
from pathlib import Path
from app.schemas import telemetry
from app.pipeline.sfm_backend import execute_sfm
from app.pipeline.georef import align
from app.camera import CameraModelType, CameraModel

input_dir = Path("workspace/HKairport01_FAST/inputs")
work = Path("workspace/HKairport01_FAST/work")
work.mkdir(parents=True, exist_ok=True)

gps = telemetry(input_dir / "gps.csv")
frames_dir = input_dir / "images"
info = {"frames": [{"name": p.name} for p in frames_dir.glob("*.jpg")]}

# We can just create a simple pinhole model
cam = CameraModel(CameraModelType.PINHOLE, 1280, 1024, 1000, 1000, 640, 512)

def dummy_progress(p, s): pass

print(f"Running SfM on {len(info['frames'])} frames...")
t0 = time.time()
reconstruction = execute_sfm(frames_dir, info, cam, dummy_progress, force_cpu=False)
t1 = time.time()
print(f"SfM Runtime: {t1 - t0:.1f} s")

(work / "poses.json").write_text(json.dumps(reconstruction["poses"]))
geo = align(reconstruction, gps, input_dir)

print(f"Registered: {len(reconstruction['poses'])}")
print(f"Sparse points: {reconstruction['sparse_points']}")
print(f"RMSE: {geo['rmse']}")
print(f"Median: {geo['median']}")
print(f"P95: {geo['p95']}")
print(f"Scale: {geo.get('scale', 1.0)}")
