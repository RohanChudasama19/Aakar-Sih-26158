import os
import sys
import time
from pathlib import Path
import traceback

from app.pipeline.runner import run_pipeline

job_id = "test_dense_fix_3"
DATA = Path("data")
job_dir = DATA / job_id
input_dir = job_dir / "inputs"
work_dir = job_dir / "work"

print(f"Starting pipeline for {job_id}...")
try:
    run_pipeline(
        input_dir=input_dir,
        work=work_dir,
        options={"profile": "FAST_QUALITY"}
    )
except Exception as e:
    print(f"Pipeline failed: {e}")
    traceback.print_exc()
