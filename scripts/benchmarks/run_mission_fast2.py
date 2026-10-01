import os
import sys
import shutil
import json
from pathlib import Path

source_work = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AAKAR-SIH26158-Surface-Fix\aakar\data\b3198000-1dd2-4a74-95ee-937f56510279\work")
target_work = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AAKAR-SIH26158-Surface-Fix\aakar\data\1ae9eba0-28ce-45d7-ada7-ed98679e8463\work")
inputs_dir = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AAKAR-SIH26158-Surface-Fix\aakar\data\1ae9eba0-28ce-45d7-ada7-ed98679e8463\inputs")

if target_work.exists():
    shutil.rmtree(target_work, ignore_errors=True)
target_work.mkdir(parents=True, exist_ok=True)

shutil.copytree(source_work / "frames", target_work / "frames")
shutil.copytree(source_work / "masks", target_work / "masks")
shutil.copytree(source_work / "originals", target_work / "originals")
shutil.copy2(source_work / "preprocess.json", target_work / "preprocess.json")

import app.pipeline.preprocess as preprocess
import app.pipeline.readiness as readiness
def dummy_extract(*args, **kwargs):
    print("Skipped extraction, using cached frames.")
    return json.loads((target_work / "preprocess.json").read_text())
preprocess.extract = dummy_extract

def dummy_readiness(*args, **kwargs):
    return {"status": "READY", "scores": {"overall_readiness_score": 100.0}, "blocking_reasons": []}
readiness.perform_analysis = dummy_readiness

from app.pipeline.runner import run_pipeline

res = run_pipeline(
    inputs_dir,
    target_work,
    options={"engine": "colmap", "use_gpu": True, "force_profile": "BALANCED"}
)
print("--- PIPELINE DONE ---")
print(json.dumps(res, indent=2))
