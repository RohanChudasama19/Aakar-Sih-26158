import subprocess
import time
from pathlib import Path
import os

dense_dir = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon\data\b3198000-1dd2-4a74-95ee-937f56510279\work\dense_balanced")
colmap_exe = r"C:\Tools\COLMAP\bin\colmap.exe"

env = {**os.environ, 'QT_QPA_PLATFORM': 'offscreen'}

def run_fusion(name, extra_args):
    out_file = dense_dir / f"fused_{name}.ply"
    cmd = [
        colmap_exe,
        "stereo_fusion",
        "--workspace_path", str(dense_dir),
        "--workspace_format", "COLMAP",
        "--input_type", "geometric",
        "--output_path", str(out_file)
    ] + extra_args
    
    t0 = time.monotonic()
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    dur = time.monotonic() - t0
    
    out_lines = result.stdout.split('\n')
    fused_pts = 0
    for line in out_lines:
        if "Fused points :" in line:
            fused_pts = line.split(":")[-1].strip()
            
    print(f"--- VARIANT {name} ---")
    print(f"Runtime: {dur:.1f}s")
    print(f"Fused points: {fused_pts}")
    print(f"Return code: {result.returncode}")

run_fusion("CURRENT", [])
run_fusion("MODERATE_FUSION", ["--StereoFusion.min_num_pixels", "4", "--StereoFusion.max_reproj_error", "3"])
run_fusion("MODERATE_PATCHMATCH_SIMULATED", ["--StereoFusion.min_num_pixels", "3"])
