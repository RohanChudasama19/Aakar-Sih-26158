import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(".").absolute()))

from app.pipeline.dense_backend import ColmapPatchMatchBackend
from app.pipeline.profiles import FAST_QUALITY_V1

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
if not work_dir.exists():
    print("Work dir not found!")
    sys.exit(1)

directory = work_dir / "frames"

# Cleanup previous dense_fast_quality to force re-run from scratch
import shutil
dq = work_dir / "dense_fast_quality"
if dq.exists():
    print(f"Removing old {dq}")
    shutil.rmtree(dq)

sfm = {
    "model_path": str(work_dir / "sparse" / "0"),
}

# Need to parse images.txt for poses to simulate sfm dictionary
poses = {}
import numpy as np
from scipy.spatial.transform import Rotation
textdir = work_dir / "sparse_txt"
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
    # dummy id based on filename
    idx = int(name.split('.')[0])
    poses[idx] = np.c_[rot, np.array(values[5:8], float)]
    i += 1

sfm["poses"] = poses

k = {}
options = {"profile": "FAST_QUALITY"}
geo = None
def progress(pct, msg):
    print(f"[{pct}%] {msg}")

backend = ColmapPatchMatchBackend()
try:
    print("Starting Dense Pass...")
    points, colors, report = backend.run(sfm, k, directory, work_dir, options, geo, progress)
    print("Dense Pass SUCCEEDED!")
    print(f"Points: {len(points)}")
except Exception as e:
    import traceback
    print("Dense Pass FAILED!")
    traceback.print_exc()

