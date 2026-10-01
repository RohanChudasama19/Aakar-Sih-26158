import os
import shutil
import subprocess
import time
from pathlib import Path
import json
import sqlite3
import numpy as np
from scipy.spatial.transform import Rotation
import csv

def run_experiment(name, overlap, quad_overlap, refine_focal, refine_extra):
    print(f"\n--- Running Experiment: {name} ---")
    work = Path(f"workspace/HKairport01_FAST_C_FINAL/work/exp_{name}").absolute()
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    
    db_src = Path("workspace/HKairport01_FAST_C_FINAL/inputs/colmap.db").absolute()
    db = work / "colmap.db"
    
    shutil.copy2(db_src, db)
    conn = sqlite3.connect(db)
    conn.execute("DELETE FROM matches")
    conn.execute("DELETE FROM two_view_geometries")
    conn.commit()
    conn.close()
    
    start_time = time.monotonic()
    
    print("Matching...")
    subprocess.run([
        r"C:\Tools\COLMAP\bin\colmap.exe", "sequential_matcher",
        "--database_path", str(db),
        "--SequentialMatching.overlap", str(overlap),
        "--SequentialMatching.quadratic_overlap", str(quad_overlap),
        "--FeatureMatching.use_gpu", "1"
    ], stdout=subprocess.DEVNULL)
    
    models = work / "sparse"
    models.mkdir(exist_ok=True)
    
    print("Mapping...")
    subprocess.run([
        r"C:\Tools\COLMAP\bin\colmap.exe", "mapper",
        "--database_path", str(db),
        "--image_path", str(Path("workspace/HKairport01_FAST_C_FINAL/inputs/images").absolute()),
        "--output_path", str(models),
        "--Mapper.ba_refine_focal_length", str(refine_focal),
        "--Mapper.ba_refine_principal_point", "0",
        "--Mapper.ba_refine_extra_params", str(refine_extra)
    ], stdout=subprocess.DEVNULL)
    
    sfm_time = time.monotonic() - start_time
    print(f"SfM Time: {sfm_time:.2f}s")
    
    choices = list(models.glob("*/images.bin"))
    if not choices:
        print("FAILED to map")
        return
    best_model_path = max(choices, key=lambda p: p.stat().st_size).parent
    textdir = work / "sparse_txt"
    textdir.mkdir(exist_ok=True)
    subprocess.run([
        r"C:\Tools\COLMAP\bin\colmap.exe", "model_converter",
        "--input_path", str(best_model_path),
        "--output_path", str(textdir),
        "--output_type", "TXT"
    ], stdout=subprocess.DEVNULL)
    
    input_dir = Path("workspace/HKairport01_FAST_C_FINAL/inputs").absolute()
    with open("data_external/mars_lvig/processed/HKairport01/FAST/frames.csv") as f:
        times = {r["filename"]: float(r["timestamp"]) for r in csv.DictReader(f)}
    
    lines = (textdir / "images.txt").read_text().splitlines()
    poses = {}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or line.startswith("#"): continue
        values = line.split()
        qw, qx, qy, qz = map(float, values[1:5])
        tx, ty, tz = map(float, values[5:8])
        rot = Rotation.from_quat([qx, qy, qz, qw]).as_matrix()
        cname = values[9]
        poses[cname] = np.c_[rot, [tx,ty,tz]]
        i += 1

    from app.schemas import telemetry
    from app.pipeline.georef import align
    gps = telemetry(input_dir / "gps.csv")
    info_files = [f.name for f in sorted((input_dir / "images").glob("*.jpg"))]
    info = {"frames": [{"name": p, "time_sec": times[p]} for p in info_files]}
    info["start_time_utc"] = 0.0
    sfm = {"poses": {idx: poses[f["name"]] for idx, f in enumerate(info["frames"]) if f["name"] in poses}}
    geo = align(sfm, info, gps, input_dir)
    origin = np.array(geo["origin"])
    
    aerorecon_centers = {}
    for cname, P in poses.items():
        C_sfm = -P[:,:3].T @ P[:,3]
        C_abs = C_sfm * geo["scale"]
        C_abs = geo["rotation"] @ C_abs
        C_abs += geo["translation"]
        C_enu = C_abs - origin
        aerorecon_centers[times[cname]] = C_enu

    uav = json.load(open(r"data_external\uavscenes\raw\HKairport01\metadata\sampleinfos_interpolated.json"))
    map_centers = {}
    for d in uav:
        t = float(d["OriginalImageName"].replace(".jpg", ""))
        mx, my, mz = d['T4x4'][0][3], d['T4x4'][1][3], d['T4x4'][2][3]
        map_centers[t] = np.array([mx, my, mz])

    pts_A, pts_M = [], []
    for t_A, c_A in aerorecon_centers.items():
        for t_M, c_M in map_centers.items():
            if abs(t_A - t_M) < 0.1:
                pts_A.append(c_A)
                pts_M.append(c_M)
                break
    pts_A = np.array(pts_A)
    pts_M = np.array(pts_M)
    
    if len(pts_A) == 0:
        print("No matching cameras")
        return
        
    def umeyama(X, Y, estimate_scale=True):
        muX = X.mean(axis=0)
        muY = Y.mean(axis=0)
        X0 = X - muX
        Y0 = Y - muY
        varX = np.var(X0, axis=0, ddof=0).sum()
        covXY = Y0.T @ X0 / X.shape[0]
        U, D, VT = np.linalg.svd(covXY)
        S = np.eye(X.shape[1])
        if np.linalg.det(U) * np.linalg.det(VT) < 0:
            S[-1, -1] = -1
        c = np.trace(np.diag(D) @ S) / varX if estimate_scale else 1.0
        R = U @ S @ VT
        t = muY - c * R @ muX
        return c, R, t

    c, R, t = umeyama(pts_A, pts_M, estimate_scale=True)
    pts_A_trans = c * (pts_A @ R.T) + t
    err = np.linalg.norm(pts_A_trans - pts_M, axis=1)
    rmse = np.sqrt(np.mean(err**2))
    
    errors = []
    points = 0
    for line in (textdir / "points3D.txt").read_text().splitlines():
        if line and not line.startswith("#"):
            v = line.split()
            errors.append(float(v[7]))
            points += 1
            
    print(f"Registered: {len(poses)}")
    print(f"Points: {points}")
    print(f"Reprojection Error: {np.mean(errors):.4f}")
    print(f"Trajectory RMSE: {rmse:.4f} m")

run_experiment("FIXED_FOCAL", 10, 1, 0, 0)
run_experiment("WIDE_MATCH", 30, 1, 1, 1)
run_experiment("FIXED_WIDE", 30, 1, 0, 0)
