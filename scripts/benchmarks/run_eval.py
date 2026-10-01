import json
import numpy as np
import open3d as o3d
from scipy.spatial.transform import Rotation
import csv
from pathlib import Path
import time
import sys

def umeyama(X, Y, estimate_scale=True):
    # X and Y are Nxd
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

def main():
    print("Loading AAKAR Cameras...")
    input_dir = Path("workspace/HKairport01_FAST_C_FINAL/inputs")
    
    # Load gps
    gps_raw = list(csv.DictReader(open(input_dir / "gps.csv")))
    info_files = [f.name for f in sorted((input_dir / "images").glob("*.jpg"))]
    with open("data_external/mars_lvig/processed/HKairport01/FAST/frames.csv") as f:
        times = {r["filename"]: float(r["timestamp"]) for r in csv.DictReader(f)}
    
    start_time_utc = 0.0
    
    # Read sparse
    lines = (input_dir / "sparse_txt" / "images.txt").read_text().splitlines()
    poses = {} # Original SfM T_camera_world
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

    # Load alignment.json if it exists? We didn't save it. So we need to recompute geo.
    from app.schemas import telemetry
    from app.pipeline.georef import align
    gps = telemetry(input_dir / "gps.csv")
    info = {"frames": [{"name": p, "time_sec": times[p]} for p in info_files]}
    info["start_time_utc"] = 0.0
    
    sfm = {"poses": {idx: poses[f["name"]] for idx, f in enumerate(info["frames"]) if f["name"] in poses}}
    geo = align(sfm, info, gps, input_dir)
    origin = np.array(geo["origin"])
    
    aakar_centers = {}
    for cname, P in poses.items():
        C_sfm = -P[:,:3].T @ P[:,3]
        C_abs = C_sfm * geo["scale"]
        C_abs = geo["rotation"] @ C_abs
        C_abs += geo["translation"]
        C_enu = C_abs - origin
        aakar_centers[times[cname]] = C_enu

    print("Loading UAVScenes Cameras...")
    uav = json.load(open(r"data_external\uavscenes\raw\HKairport01\metadata\sampleinfos_interpolated.json"))
    map_centers = {}
    for d in uav:
        t = float(d["OriginalImageName"].replace(".jpg", ""))
        mx, my, mz = d['T4x4'][0][3], d['T4x4'][1][3], d['T4x4'][2][3]
        map_centers[t] = np.array([mx, my, mz])

    print("Matching cameras...")
    pts_A = []
    pts_M = []
    for t_A, c_A in aakar_centers.items():
        for t_M, c_M in map_centers.items():
            if abs(t_A - t_M) < 0.1:
                pts_A.append(c_A)
                pts_M.append(c_M)
                break
    
    pts_A = np.array(pts_A)
    pts_M = np.array(pts_M)
    print(f"Matched {len(pts_A)} cameras")
    
    c, R, t = umeyama(pts_A, pts_M, estimate_scale=True)
    pts_A_trans = c * (pts_A @ R.T) + t
    err = np.linalg.norm(pts_A_trans - pts_M, axis=1)
    rmse = np.sqrt(np.mean(err**2))
    print(f"Sim3 Scale: {c:.4f}")
    print(f"Sim3 Trajectory RMSE: {rmse:.4f} m")

    print("Loading AAKAR fused.ply...")
    work = Path("workspace/HKairport01_FAST_C_FINAL/work")
    ply_path = work / "dense_fast" / "fused.ply"
    pcd_A = o3d.io.read_point_cloud(str(ply_path))
    # Transform fused.ply to Map frame.
    # fused.ply is in SfM frame!
    # Wait, in the dense script we did:
    # local_pts = points - origin.
    # But fused.ply points are directly from COLMAP, so they are in SfM frame!
    pts_sfm = np.asarray(pcd_A.points)
    pts_abs = pts_sfm * geo["scale"]
    pts_abs = pts_abs @ np.array(geo["rotation"]).T
    pts_abs += np.array(geo["translation"])
    pts_enu = pts_abs - origin
    
    pts_enu_trans = c * (pts_enu @ R.T) + t
    pcd_A.points = o3d.utility.Vector3dVector(pts_enu_trans)
    
    print("Loading Map Cloud...")
    map_path = r"data_external\mars_lvig\raw\HKairport01\reference\cloud_merged.ply"
    pcd_M = o3d.io.read_point_cloud(map_path)
    
    # Footprint crop
    vmin = pts_enu_trans.min(axis=0) - 20.0
    vmax = pts_enu_trans.min(axis=0) + 20.0 # Wait, vmax should be max!
    vmax = pts_enu_trans.max(axis=0) + 20.0
    print("Cropping map cloud...")
    bbox = o3d.geometry.AxisAlignedBoundingBox(vmin, vmax)
    pcd_M_crop = pcd_M.crop(bbox)
    
    # Downsample for speed if needed
    pcd_A_down = pcd_A.voxel_down_sample(0.25)
    pcd_M_down = pcd_M_crop.voxel_down_sample(0.25)
    
    pts_A_arr = np.asarray(pcd_A_down.points)
    pts_M_arr = np.asarray(pcd_M_down.points)
    print(f"AAKAR points: {len(pts_A_arr)}, Reference points in footprint: {len(pts_M_arr)}")
    
    print("Computing A -> M distances...")
    tree_M = o3d.geometry.KDTreeFlann(pcd_M_down)
    dists_A_to_M = []
    for p in pts_A_arr:
        _, idx, sq = tree_M.search_knn_vector_3d(p, 1)
        dists_A_to_M.append(np.sqrt(sq[0]))
    
    d_AM = np.array(dists_A_to_M)
    rmse_3d = np.sqrt(np.mean(d_AM**2))
    print(f"A->M RMSE 3D: {rmse_3d:.4f} m")
    print(f"A->M MAE: {np.mean(d_AM):.4f} m")
    print(f"A->M median: {np.median(d_AM):.4f} m")
    print(f"A->M P95: {np.percentile(d_AM, 95):.4f} m")
    print(f"A->M P99: {np.percentile(d_AM, 99):.4f} m")
    print(f"A->M max: {np.max(d_AM):.4f} m")
    
    print("Computing M -> A distances...")
    tree_A = o3d.geometry.KDTreeFlann(pcd_A_down)
    dists_M_to_A = []
    for p in pts_M_arr:
        _, idx, sq = tree_A.search_knn_vector_3d(p, 1)
        dists_M_to_A.append(np.sqrt(sq[0]))
        
    d_MA = np.array(dists_M_to_A)
    c25 = np.sum(d_MA <= 0.25) / len(d_MA) * 100
    c50 = np.sum(d_MA <= 0.50) / len(d_MA) * 100
    c100 = np.sum(d_MA <= 1.00) / len(d_MA) * 100
    c200 = np.sum(d_MA <= 2.00) / len(d_MA) * 100
    
    print(f"Completeness < 0.25m: {c25:.2f}%")
    print(f"Completeness < 0.50m: {c50:.2f}%")
    print(f"Completeness < 1.00m: {c100:.2f}%")
    print(f"Completeness < 2.00m: {c200:.2f}%")
    
    print("Doing ICP Diagnostic...")
    reg = o3d.pipelines.registration.registration_icp(
        pcd_A_down, pcd_M_down, 2.0, np.eye(4),
        o3d.pipelines.registration.TransformationEstimationPointToPoint()
    )
    print(f"ICP RMSE: {reg.inlier_rmse:.4f} m")
    print(f"ICP Fitness: {reg.fitness:.4f}")
    
    # Output to json to load later
    res = {
        "matched": len(pts_A),
        "scale": c,
        "traj_rmse": rmse,
        "A_pts": len(pts_A_arr),
        "M_pts": len(pts_M_arr),
        "rmse_3d": rmse_3d,
        "mae": float(np.mean(d_AM)),
        "median": float(np.median(d_AM)),
        "p95": float(np.percentile(d_AM, 95)),
        "p99": float(np.percentile(d_AM, 99)),
        "max": float(np.max(d_AM)),
        "c25": c25,
        "c50": c50,
        "c100": c100,
        "c200": c200,
        "icp_rmse": reg.inlier_rmse,
        "icp_fitness": reg.fitness
    }
    with open("eval_results.json", "w") as f:
        json.dump(res, f)

if __name__ == '__main__':
    main()
