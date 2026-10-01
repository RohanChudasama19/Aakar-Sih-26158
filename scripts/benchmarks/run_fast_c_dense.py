import time
import subprocess
from pathlib import Path
import json
import numpy as np
import shutil
import cv2
import csv
from scipy.spatial.transform import Rotation
from app.camera import CameraModelType, CameraModel
from app.schemas import telemetry
from app.pipeline.georef import align
from app.pipeline.dense_backend import execute_dense
from app.pipeline.mesh import build_mesh
from app.pipeline.texture import texture_mesh

def run_dense_benchmark():
    print("--- DENSE BENCHMARK FAST_C ---")
    
    t_start = time.time()
    
    # 1. SETUP
    input_dir = Path("workspace/HKairport01_FAST_C_FINAL/inputs")
    work = Path("workspace/HKairport01_FAST_C_FINAL/work")
    dense_dir = work / "dense"
    
    gps = telemetry(input_dir / "gps.csv")
    frames_dir = input_dir / "images"
    info = {"frames": [{"name": p.name} for p in sorted(frames_dir.glob("*.jpg"))]}
    
    with open("data_external/mars_lvig/processed/HKairport01/FAST/frames.csv") as f:
        times = {r["filename"]: float(r["timestamp"]) for r in csv.DictReader(f)}
    for fr in info["frames"]:
        fr["time_sec"] = times[fr["name"]]
    info["start_time_utc"] = 0.0
    
    scale_factor = 1024 / 2448.0
    w = int(2448 * scale_factor)
    h = int(2048 * scale_factor)
    cam = CameraModel(CameraModelType.PINHOLE, w, h, 600, 600, w//2, h//2)
    
    textdir = input_dir / "sparse_txt"
    poses = {}
    lines = (textdir / "images.txt").read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or line.startswith("#"): continue
        values = line.split()
        qw, qx, qy, qz = map(float, values[1:5])
        rot = Rotation.from_quat([qx, qy, qz, qw]).as_matrix()
        cname = values[9]
        idx = next((n for n, f in enumerate(info["frames"]) if f["name"] == cname), None)
        if idx is not None:
            poses[idx] = np.c_[rot, np.array(values[5:8], float)]
        i += 1
        
    points_3d = []
    with open(textdir / "points3D.txt") as f:
        for line in f:
            if line.startswith("#"): continue
            points_3d.append(line.split()[1:4])
            
    sfm = {
        "poses": poses,
        "model_path": str(input_dir / "sparse" / "0"),
        "points": np.array(points_3d, float)
    }
    
    geo = align(sfm, info, gps, input_dir)
    
    opts = {
        "profile": "FAST",
        "force_profile": "FAST", # For dense_backend
        "mesh_decimation": 50000,
        "texture_resolution": 2048,
        "max_image_size": 1024
    }
    
    def dummy_prog(p, s):
        print(f"[{p}%] {s}")
        
    t_prep = time.time()
    
    print("Executing Dense...")
    t0_dense = time.time()
    
    # We will override the backend to enable geometric consistency in FAST profile if asked.
    import app.pipeline.colmap as colmap_mod
    orig_run = colmap_mod.run
    def run_colmap_override(args, work_dir):
        args = [str(a) for a in args]
        if "patch_match_stereo" in args:
            # Enable geom consistency for FAST mode
            for i, a in enumerate(args):
                if a == "--PatchMatchStereo.geom_consistency":
                    args[i+1] = "1"
        try:
            subprocess.run(args, check=True)
        except subprocess.CalledProcessError as e:
            print(f"FAILED. Return code {e.returncode}")
            raise
    colmap_mod.run = run_colmap_override
    
    try:
        points, colors, dense_report = execute_dense(sfm, cam.to_matrix(), frames_dir, work, opts, geo, dummy_prog)
    finally:
        colmap_mod.run = orig_run
        
    t_dense = time.time() - t0_dense
    
    print("Mapping undistorted images for texture.py...")
    dense_images = dense_dir / "images"
    for idx, fr in enumerate(info["frames"]):
        orig_name = fr["name"]
        undist_path = dense_images / orig_name
        target_path = dense_images / f"{idx:06d}.png"
        if undist_path.exists():
            img = cv2.imread(str(undist_path))
            if img is not None:
                cv2.imwrite(str(target_path), img)
                
    print("Executing Mesh & Texture...")
    t0_mesh = time.time()
    
    from app.pipeline.surface import reconstruct_surface
    local_pts = points - np.array(geo["origin"])
    cameras = np.array([-p[:, :3].T @ p[:, 3] for p in sfm["poses"].values()])
    cameras = cameras - np.array(geo["origin"])
    
    mesh = reconstruct_surface(local_pts, cameras)
    out_mesh = texture_mesh(mesh, geo, sfm, cam.to_matrix(), dense_images, opts)
    if not out_mesh:
        out_mesh = mesh
    
    t_mesh = time.time() - t0_mesh
    
    print("Executing Export...")
    t0_export = time.time()
    import trimesh
    glb_path = work / "model.glb"
    out_mesh.export(glb_path)
    ply_path = work / "dense_filtered.ply"
    trimesh.points.PointCloud(points, colors=colors).export(ply_path)
    t_export = time.time() - t0_export
    
    t_total = time.time() - t_start
    
    print("\n==============================")
    print("BENCHMARK RESULTS")
    print(f"Preparation: {t_prep - t_start:.2f} s")
    print(f"Dense Total: {t_dense:.2f} s")
    print(f"  Undistort: {dense_report.get('subprocess_timings', {}).get('undistort_s', 0)} s")
    print(f"  PatchMatch: {dense_report.get('subprocess_timings', {}).get('patchmatch_s', 0)} s")
    print(f"  Fusion: {dense_report.get('subprocess_timings', {}).get('fusion_s', 0)} s")
    print(f"Mesh/Texture: {t_mesh:.2f} s")
    print(f"Export: {t_export:.2f} s")
    print(f"Total Usable Model Time: {t_total:.2f} s")
    
    print("\nDENSE REPORT:")
    print(json.dumps(dense_report, indent=2))
    
    print("\nOUTPUT FILES:")
    print(f"GLB: {glb_path.stat().st_size / 1024**2:.2f} MB")
    print(f"PLY: {ply_path.stat().st_size / 1024**2:.2f} MB")
    
if __name__ == "__main__":
    run_dense_benchmark()
