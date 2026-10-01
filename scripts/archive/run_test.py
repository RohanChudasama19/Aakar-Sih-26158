import os
import sys
import time
from pathlib import Path

from app.pipeline.runner import run_pipeline

job_id = "test_dense_fix_3"
DATA = Path("data")
job_dir = DATA / job_id
input_dir = job_dir / "inputs"
work_dir = job_dir / "work"
input_dir.mkdir(parents=True, exist_ok=True)

import shutil
src_colorado = Path("colorado_dataset")
for f in src_colorado.glob("*"):
    if f.is_file():
        shutil.copy2(f, input_dir / f.name)

if (input_dir / "flight_metadata.json").exists():
    (input_dir / "flight_metadata.json").unlink()

print(f"Starting pipeline for {job_id}...")
try:
    run_pipeline(
        input_dir=input_dir,
        work=work_dir,
        options={"profile": "FAST_QUALITY"}
    )
except Exception as e:
    print(f"Pipeline failed: {e}")
