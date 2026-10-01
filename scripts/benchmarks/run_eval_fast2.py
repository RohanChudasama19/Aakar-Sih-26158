import json
import numpy as np
import open3d as o3d
from scipy.spatial.transform import Rotation
import csv
from pathlib import Path

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

print("Starting eval...")
input_dir = Path("workspace/HKairport01_FAST_C_FINAL/inputs")
info_files = [f.name for f in sorted((input_dir / "images").glob("*.jpg"))]
with open("data_external/mars_lvig/processed/HKairport01/FAST/frames.csv") as f:
    times = {r["filename"]: float(r["timestamp"]) for r in csv.DictReader(f)}

lines = (input_dir / "sparse_txt" / "images.txt").read_text().splitlines()
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
c, R, t = umeyama(pts_A, pts_M, estimate_scale=True)
pts_A_trans = c * (pts_A @ R.T) + t
err = np.linalg.norm(pts_A_trans - pts_M, axis=1)
rmse = np.sqrt(np.mean(err**2))
print("Alignment computed.")

pcd_A = o3d.io.read_point_cloud(str(Path("workspace/HKairport01_FAST_C_FINAL/work/dense_fast/fused.ply")))
pts_sfm = np.asarray(pcd_A.points)
pts_abs = pts_sfm * geo["scale"]
pts_abs = pts_abs @ np.array(geo["rotation"]).T
pts_abs += np.array(geo["translation"])
pts_enu = pts_abs - origin
pts_enu_trans = c * (pts_enu @ R.T) + t
pcd_A.points = o3d.utility.Vector3dVector(pts_enu_trans)

print("Reading full map cloud...")
pcd_M = o3d.io.read_point_cloud(r"data_external\mars_lvig\raw\HKairport01\reference\cloud_merged.ply")
vmax = pts_enu_trans.max(axis=0) + 20.0
vmin = pts_enu_trans.min(axis=0) - 20.0
print("Cropping...")
pcd_M_crop = pcd_M.crop(o3d.geometry.AxisAlignedBoundingBox(vmin, vmax))

print("Downsampling to 0.5m...")
pcd_A_down = pcd_A.voxel_down_sample(0.50)
pcd_M_down = pcd_M_crop.voxel_down_sample(0.50)

print("Computing distance A->M...")
d_AM = np.asarray(pcd_A_down.compute_point_cloud_distance(pcd_M_down))
rmse_3d = np.sqrt(np.mean(d_AM**2))

print("Computing distance M->A...")
d_MA = np.asarray(pcd_M_down.compute_point_cloud_distance(pcd_A_down))
c25 = np.sum(d_MA <= 0.25) / len(d_MA) * 100
c50 = np.sum(d_MA <= 0.50) / len(d_MA) * 100
c100 = np.sum(d_MA <= 1.00) / len(d_MA) * 100
c200 = np.sum(d_MA <= 2.00) / len(d_MA) * 100

print("ICP...")
reg = o3d.pipelines.registration.registration_icp(
    pcd_A_down, pcd_M_down, 2.0, np.eye(4),
    o3d.pipelines.registration.TransformationEstimationPointToPoint()
)

res = {
    "matched": len(pts_A),
    "scale": c,
    "traj_rmse": rmse,
    "A_pts": len(np.asarray(pcd_A_down.points)),
    "M_pts": len(np.asarray(pcd_M_down.points)),
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
with open("eval_results_fast.json", "w") as f:
    json.dump(res, f)
print("Done!")
