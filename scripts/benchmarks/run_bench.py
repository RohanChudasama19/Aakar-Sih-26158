import os
import shutil
from pathlib import Path
from app.pipeline.runner import run_pipeline

def run_prof(prof_name):
    base_dir = Path(f"workspace/bench_{prof_name}")
    if base_dir.exists(): shutil.rmtree(base_dir)
    base_dir.mkdir(parents=True)
    
    in_dir = base_dir / "inputs"
    in_dir.mkdir()
    
    shutil.copy("samples/sample.mp4", in_dir / "video.mp4")
    shutil.copy("samples/gps.csv", in_dir / "gps.csv")
    shutil.copy("samples/flight.json", in_dir / "flight.json")
    
    opts = {"max_frames": 20, "max_width": 640, "force_profile": prof_name, "engine": "colmap"}
    
    rep = run_pipeline(in_dir, base_dir / "work", opts)
    print(f"--- {prof_name} ---")
    print(f"Time: {rep.get('processing_time_sec')}")
    print(f"Registered: {rep.get('targets',{}).get('coverage',{}).get('registered_frames')}")
    print(f"Dense points: {rep.get('dense',{}).get('dense_points_count')}")
    print(f"Peak VRAM: {rep.get('dense',{}).get('peak_vram_gb')}")
    print(f"Peak RAM: {rep.get('dense',{}).get('peak_ram_gb')}")

if __name__ == "__main__":
    run_prof("FAST")
    run_prof("BALANCED")
    run_prof("QUALITY")
