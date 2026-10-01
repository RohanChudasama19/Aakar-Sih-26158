import os
import subprocess
import shutil
from pathlib import Path
from app.pipeline.runner import run_pipeline

def main():
    base_dir = Path("workspace/ab_test")
    if base_dir.exists(): shutil.rmtree(base_dir)
    base_dir.mkdir(parents=True)
    
    in_dir = base_dir / "inputs"
    in_dir.mkdir()
    
    shutil.copy("samples/sample.mp4", in_dir / "video.mp4")
    shutil.copy("samples/gps.csv", in_dir / "gps.csv")
    shutil.copy("samples/flight.json", in_dir / "flight.json")
    
    opts_base = {"max_frames": 20, "max_width": 640, "test_dynamic": False}
    opts_mask = {"max_frames": 20, "max_width": 640, "test_dynamic": True} # Wait, `test_dynamic` is a debug flag inside semantic.py!
    
    print("Running baseline...")
    rep_base = run_pipeline(in_dir, base_dir / "work_base", opts_base)
    print("Running masked...")
    rep_mask = run_pipeline(in_dir, base_dir / "work_mask", opts_mask)
    
    print("Baseline dynamic masked:", rep_base["semantics"].get("dynamic_objects_masked"))
    print("Masked dynamic masked:", rep_mask["semantics"].get("dynamic_objects_masked"))
    
if __name__ == "__main__":
    main()
