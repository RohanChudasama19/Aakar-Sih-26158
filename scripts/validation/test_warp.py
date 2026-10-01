import os
import shutil
import subprocess
import time
from pathlib import Path
import json
import sqlite3
import numpy as np
from scipy.spatial.transform import Rotation
import csv

input_dir = Path("workspace/HKairport01_FAST_C_FINAL/inputs").absolute()
src_sparse = Path("workspace/HKairport01_FAST_C_FINAL/work/sparse_txt").absolute()

from app.schemas import telemetry
from app.pipeline.georef import align
gps = telemetry(input_dir / "gps.csv")
with open("data_external/mars_lvig/processed/HKairport01/FAST/frames.csv") as f:
    times = {r["filename"]: float(r["timestamp"]) for r in csv.DictReader(f)}

lines = (src_sparse / "images.txt").read_text().splitlines()
poses = {}
i = 0
while i < len(lines):
    line = lines[i].strip()
    i += 1
    if not line or line.startswith("#"): continue
    values = line.split()
    qw, qx, qy, qz = map(float, values[1:5])
    tx, ty, tz = map(float, values[5:8])
    rot = Rotation.from_quat([qx, qy, qz, qw]).as_matrix()
    cname = values[9]
    poses[cname] = np.c_[rot, [tx,ty,tz]]
    i += 1

info_files = [f.name for f in sorted((input_dir / "images").glob("*.jpg"))]
info = {"frames": [{"name": p, "time_sec": times[p]} for p in info_files]}
info["start_time_utc"] = 0.0
sfm = {"poses": {idx: poses[f["name"]] for idx, f in enumerate(info["frames"]) if f["name"] in poses}}

geo = align(sfm, info, gps, input_dir)
origin = np.array(geo["origin"])

# Wait, georef.align rigidly aligned the model to GPS.
# We want to warp the cameras to match the exact GPS, then un-align them back to SfM frame, or just run BA in the Geo frame!
# Bundle adjuster can run on any frame. Let's transform all poses AND points to the Geo frame, THEN apply non-rigid warp to GPS, then BA.
