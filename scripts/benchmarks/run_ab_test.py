import os
import subprocess
import shutil
from pathlib import Path

def run_cmd(cmd):
    print(f"Running: {cmd}")
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        print("FAILED")

def main():
    # Setup inputs
    input_dir = Path("data_external/uavid/converted/val/seq18/Images")
    
    out_base = Path("workspace/dynamic_ab/baseline")
    out_mask = Path("workspace/dynamic_ab/masked")
    
    if out_base.exists(): shutil.rmtree(out_base)
    if out_mask.exists(): shutil.rmtree(out_mask)
    
    # 1. Baseline Run (Masking OFF)
    print("=== BASELINE ===")
    cmd = (
        f".\\.venv\\Scripts\\python app/pipeline/runner.py "
        f"--input \"{input_dir}\" --output \"{out_base}\" "
        f"--quality low --dense --no-semantic --use-relative"
    )
    run_cmd(cmd)
    
    # 2. Masked Run (Masking ON)
    print("=== MASKED ===")
    cmd = (
        f".\\.venv\\Scripts\\python app/pipeline/runner.py "
        f"--input \"{input_dir}\" --output \"{out_mask}\" "
        f"--quality low --dense --semantic --use-relative"
    )
    run_cmd(cmd)

if __name__ == "__main__":
    main()
