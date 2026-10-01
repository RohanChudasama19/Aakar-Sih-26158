import sys, csv, json, shutil, time, struct, os, hashlib, subprocess
import numpy as np
from pathlib import Path
from scipy.spatial.transform import Rotation

sys.path.insert(0, str(Path.cwd()))
from app.pipeline.colmap import resolve_colmap_executable, get_colmap_env, run as colmap_run
from app.pipeline import colmap as colmap_mod

# ============================================================
# PHASE 1 REPORT: Pipeline Input Compatibility
# ============================================================
print("=" * 60)
print("PHASE 1: INPUT COMPATIBILITY")
print("=" * 60)
print("Production runner.py requires cv2.VideoCapture on a video file.")
print("Image-directory input: NOT natively supported.")
print("Action: Standalone diagnostic script calling colmap.sparse,")
print("        dense_backend.ColmapPatchMatchBackend, and surface.reconstruct_surface")
print("        directly with frame-based inputs. No video fabricated.")
print("Label: FRAME-BASED RECONSTRUCTION")
print()

# Source dataset
mars_dir = Path("data_external/mars_lvig/processed/HKairport01/FAST")
images_src = mars_dir / "images"
gps_csv = mars_dir / "gps.csv"

frames = sorted(images_src.glob("frame_*.jpg"))
print(f"Available frames: {len(frames)}")

# Read GPS
gps_rows = list(csv.DictReader(gps_csv.open()))
print(f"GPS records: {len(gps_rows)}")

# Read timestamps
timestamps = [float(r['timestamp']) for r in gps_rows]
intervals = [timestamps[i+1]-timestamps[i] for i in range(len(timestamps)-1)]
avg_interval = sum(intervals)/len(intervals)
eff_fps = 1.0/avg_interval
print(f"Timestamp range: {timestamps[0]:.2f} to {timestamps[-1]:.2f}")
print(f"Avg interval: {avg_interval:.3f}s -> Effective FPS: {eff_fps:.2f}")
print(f"GPS-frame alignment: {len(frames)} frames, {len(gps_rows)} GPS rows, delta={len(frames)-len(gps_rows)}")
print()
print("Camera intrinsics provenance: ESTIMATED from COLMAP (no calibration file present)")
print("Missing telemetry: IMU (not available), LiDAR (used as reference only, not input)")
print("Processing mode: FRAME-BASED RECONSTRUCTION (not full video ingestion)")
