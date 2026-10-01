import os
import sys
import time
from pathlib import Path

from app.pipeline.runner import run_pipeline

job_id = "test_dense_fix_5"
DATA = Path("data")
job_dir = DATA / job_id
input_dir = job_dir / "inputs"
work_dir = job_dir / "work"
input_dir.mkdir(parents=True, exist_ok=True)

import shutil
src = Path("data/b83295bd-9419-485c-bdee-8dce65de4f7c/inputs")
for f in src.glob("*"):
    if f.is_file():
        shutil.copy2(f, input_dir / f.name)

# Ensure no bad frames in preprocess! Wait, we will just use the pre-extracted frames!
shutil.copytree("data/b83295bd-9419-485c-bdee-8dce65de4f7c/work/frames", work_dir / "frames")
shutil.copytree("data/b83295bd-9419-485c-bdee-8dce65de4f7c/work/originals", work_dir / "originals")
shutil.copytree("data/b83295bd-9419-485c-bdee-8dce65de4f7c/work/masks", work_dir / "masks")
shutil.copy2("data/b83295bd-9419-485c-bdee-8dce65de4f7c/work/preprocess.json", work_dir / "preprocess.json")
shutil.copy2("data/b83295bd-9419-485c-bdee-8dce65de4f7c/work/flight_info.json", work_dir / "flight_info.json")

print("Running pipeline from SfM onwards...")
