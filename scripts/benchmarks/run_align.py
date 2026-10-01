import csv
import json
import numpy as np
from pathlib import Path
from scipy.spatial.transform import Rotation
from app.schemas import telemetry
from app.pipeline.georef import align

input_dir = Path("workspace/HKairport01_FAST/inputs")
gps = telemetry(input_dir / "gps.csv")
frames_dir = input_dir / "images"
info = {"frames": [{"name": p.name} for p in frames_dir.glob("*.jpg")]}

with open("data_external/mars_lvig/processed/HKairport01/FAST/frames.csv") as f:
    for r in csv.DictReader(f):
        for fr in info["frames"]:
            if fr["name"] == r["filename"]:
                fr["time_sec"] = float(r["timestamp"])

info["start_time_utc"] = 0.0

textdir = input_dir / "sparse_txt"
poses = {}
lines = (textdir / "images.txt").read_text().splitlines()
i = 0
while i < len(lines):
    line = lines[i].strip()
    i += 1
    if not line or line.startswith("#"):
        continue
    values = line.split()
    qw, qx, qy, qz = map(float, values[1:5])
    rot = Rotation.from_quat([qx, qy, qz, qw]).as_matrix()
    name = values[9]
    idx = next((n for n, f in enumerate(info["frames"]) if f["name"] == name), None)
    if idx is not None:
        poses[idx] = np.c_[rot, np.array(values[5:8], float)]
    i += 1

reconstruction = {"poses": poses}
geo = align(reconstruction, info, gps, input_dir)
print(f"Registered: {len(poses)}")
print(f"RMSE: {geo.get('rmse_m')}")
print(f"Scale: {geo.get('scale')}")
