
from pathlib import Path
import shutil
import json
import time
import os

jid = "FAST_VALIDATION"
job_dir = Path("data") / jid
if job_dir.exists():
    shutil.rmtree(job_dir)

input_dir = job_dir / "inputs"
input_dir.mkdir(parents=True)
work_dir = job_dir / "work"

src_dir = Path("data/ab067831-368b-4087-a43e-11a08ee0ae74/inputs")
for f in src_dir.iterdir():
    shutil.copy2(f, input_dir / f.name)

from app.pipeline.runner import run_pipeline

options = {
    "force_profile": "FAST",
    "use_gpu": True,
    "max_frames": 250
}

def cb(stage, p, msg):
    print(f"[{stage}] {p}%: {msg}")

print("Starting pipeline...")
try:
    run_pipeline(input_dir, work_dir, options, cb)
    print("Pipeline completed.")
except Exception as e:
    import traceback
    traceback.print_exc()

