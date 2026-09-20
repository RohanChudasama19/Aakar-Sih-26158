import csv
from enum import Enum
from pathlib import Path
import json

import numpy as np
from pyproj import Transformer


class MetricState(str, Enum):
    RELATIVE = "RELATIVE"
    METRIC_SCALE = "METRIC_SCALE"
    GEOREFERENCED_METRIC = "GEOREFERENCED_METRIC"
    GCP_GEOREFERENCED = "GCP_GEOREFERENCED"


def similarity(a, b):
    ac, bc = a - a.mean(0), b - b.mean(0)
    if np.linalg.matrix_rank(ac, tol=1e-5) < 2:
        return 1.0, np.eye(3), np.zeros(3)

    u, d, vt = np.linalg.svd(bc.T @ ac / len(a))
    sign = np.ones(3)
    sign[-1] = np.sign(np.linalg.det(u @ vt))
    r = u @ np.diag(sign) @ vt

    var_a = np.mean(np.sum(ac * ac, axis=1))
    if var_a < 1e-9:
        scale = 1.0
    else:
        scale = np.sum(d * sign) / var_a

    t = b.mean(0) - scale * r @ a.mean(0)
    return scale, r, t


def _try_gcp_alignment(input_dir, epsg):
    cp_path = input_dir / "checkpoints.csv"
    if not cp_path.exists():
        return None
        
    try:
        from app.pipeline.accuracy_validation import parse_checkpoint_csv
        cps = parse_checkpoint_csv(cp_path)
        
        from app.pipeline.control_geometry import GroundControlPoint, ControlRole, VerticalDatum, fit_control_alignment
        
        gcps = []
        for c in cps:
            if c.get("recon_x") is not None:
                role = ControlRole.CONTROL if c.get("role", "").upper() == "CONTROL" else ControlRole.CHECKPOINT
                vd_str = c.get("vertical_datum", "UNKNOWN").upper()
                try:
                    vd = VerticalDatum(vd_str)
                except ValueError:
                    vd = VerticalDatum.UNKNOWN
                    
                gcps.append(GroundControlPoint(
                    checkpoint_id=c["checkpoint_id"],
                    latitude=c["latitude"],
                    longitude=c["longitude"],
                    elevation=c["elevation"],
                    role=role,
                    recon_x=c["recon_x"],
                    recon_y=c["recon_y"],
                    recon_z=c["recon_z"],
                    vertical_datum=vd,
                    reference_accuracy_horizontal_m=c.get("reference_accuracy_horizontal_m") or 0.05,
                    reference_accuracy_vertical_m=c.get("reference_accuracy_vertical_m") or 0.1,
                    survey_method=c.get("survey_method") or "UNKNOWN"
                ))
                
        control_count = sum(1 for g in gcps if g.role == ControlRole.CONTROL)
        if control_count > 0:
            if control_count < 4:
                return {
                    "valid": False,
                    "metric_state": MetricState.RELATIVE.value,
                    "reason": f"NOT_ENOUGH_CONTROLS: Minimum 4 valid CONTROL points required (found {control_count}). Recommended 6-10.",
                    "scale": 1.0,
                    "rotation": np.eye(3).tolist(),
                    "translation": np.zeros(3).tolist(),
                    "origin": [0.0, 0.0, 0.0],
                    "epsg": epsg,
                    "coordinate_system": "UTM",
                    "rmse_m": None,
                }
                
            rep = fit_control_alignment(gcps, input_dir, epsg)
            
            return {
                "valid": True,
                "metric_state": MetricState.GCP_GEOREFERENCED.value,
                "scale": rep["transform"]["scale"],
                "rotation": rep["transform"]["rotation"],
                "translation": rep["transform"]["translation"],
                "origin": [0.0, 0.0, 0.0],
                "epsg": epsg,
                "coordinate_system": "UTM",
                "rmse_m": rep["CONTROL_FIT_RMSE"],
                "alignment_inliers": rep["robust_inliers"],
                "alignment_samples": rep["control_count"],
                "gps_residuals_m": [d["residual_m"] for d in rep["control_residuals"]],
                "rtk_used": False,
                "barometer_used": False,
                "checkpoint_rmse_3d": None,
                "position_source": "GCP",
                "gcp_report": rep
            }
            
    except Exception as e:
        print(f"Failed to run GCP alignment: {e}")
        
    return None

def align(sfm, info, gps, input_dir):
    start_time_utc = info.get("start_time_utc", 0.0)

    # Establish UTM Projection
    lat0, lon0, alt0 = gps[0]["latitude"], gps[0]["longitude"], gps[0]["altitude_m"]
    zone = min(60, max(1, int((lon0 + 180) // 6) + 1))
    epsg = (32600 if lat0 >= 0 else 32700) + zone
    
    # Check GCP alignment first (Precedence: CONTROL > RTK > GNSS)
    gcp_res = _try_gcp_alignment(input_dir, epsg)
    if gcp_res is not None:
        return gcp_res

    tx = Transformer.from_crs(4326, epsg, always_xy=True)

    # Process GPS timeline
    gps_times = np.array([s["time"] for s in gps])
    e, n = tx.transform([s["longitude"] for s in gps], [s["latitude"] for s in gps])

    absolute_coords = np.c_[e, n, [s["altitude_m"] for s in gps]]
    origin = absolute_coords[0].copy()

    enu_coords = absolute_coords - origin
    
    position_source = "GNSS_SINGLE"

    rtk_used = False
    correction = input_dir / "rtk.csv"
    if correction.exists():
        with correction.open() as f:
            rows = list(csv.DictReader(f))

        if "timestamp_utc" in rows[0]:
            from datetime import datetime
            rtk_times = np.array(
                [datetime.fromisoformat(r["timestamp_utc"].replace("Z", "+00:00")).timestamp() for r in rows]
            )
        else:
            rtk_times = np.array([float(r["frame"]) / info["fps"] + start_time_utc for r in rows])

        x = np.array(
            [[float(r["east_correction_m"]), float(r["north_correction_m"]), float(r["up_correction_m"])] for r in rows]
        )

        if len(x) >= 2:
            for d in range(3):
                enu_coords[:, d] += np.interp(gps_times, rtk_times, x[:, d])
            rtk_used = True
            position_source = "RTK_FLOAT"

    baro_used = False
    baro = input_dir / "barometer.csv"
    if baro.exists():
        with baro.open() as f:
            rows = list(csv.DictReader(f))

        if "timestamp_utc" in rows[0]:
            from datetime import datetime
            baro_times = np.array(
                [datetime.fromisoformat(r["timestamp_utc"].replace("Z", "+00:00")).timestamp() for r in rows]
            )
        else:
            baro_times = np.array([float(r["frame"]) / info["fps"] + start_time_utc for r in rows])

        x = np.array([float(r["altitude_m"]) for r in rows])

        if len(x) >= 2:
            enu_coords[:, 2] = np.interp(gps_times, baro_times, x) - alt0
            baro_used = True

    ids = sorted(sfm["poses"].keys())
    frame_times = []
    centers = []

    for i in ids:
        frame_dict = info["frames"][i]
        t = start_time_utc + frame_dict["time_sec"]

        if gps_times[0] <= t <= gps_times[-1]:
            frame_times.append(t)
            centers.append(-sfm["poses"][i][:, :3].T @ sfm["poses"][i][:, 3])

    if len(centers) < 3:
        return {
            "valid": False,
            "metric_state": MetricState.RELATIVE.value,
            "reason": "Insufficient synchronized registered frames for Sim(3) alignment.",
            "scale": 1.0,
            "rotation": np.eye(3).tolist(),
            "translation": np.zeros(3).tolist(),
            "origin": origin.tolist(),
            "epsg": epsg,
            "coordinate_system": "UTM",
            "rmse_m": None,
        }

    centers = np.array(centers)
    frame_times = np.array(frame_times)
    targets = np.zeros((len(frame_times), 3))
    for d in range(3):
        targets[:, d] = np.interp(frame_times, gps_times, enu_coords[:, d])

    eig = np.linalg.svd(targets - targets.mean(0), compute_uv=False)
    if eig[0] < 0.5 or eig[1] / eig[0] < 0.015:
        return {
            "valid": False,
            "metric_state": MetricState.RELATIVE.value,
            "reason": "GPS trajectory is stationary or nearly collinear; absolute orientation underconstrained.",
            "scale": 1.0,
            "rotation": np.eye(3).tolist(),
            "translation": np.zeros(3).tolist(),
            "origin": origin.tolist(),
            "epsg": epsg,
            "coordinate_system": "UTM",
            "rmse_m": None,
        }

    from app.pipeline.sensor_fusion import PositionPrior, robust_position_alignment, GNSSQuality, compute_sigma
    gnss_priors = []
    for idx in range(len(centers)):
        q = GNSSQuality.RTK_FLOAT if rtk_used else GNSSQuality.DGPS
        cx, cy, cz, is_meas = compute_sigma(q, None, None, None)
        gnss_priors.append(
            PositionPrior(
                timestamp=frame_times[idx],
                x=targets[idx][0],
                y=targets[idx][1],
                z=targets[idx][2],
                quality=q,
                sigma_x=cx, sigma_y=cy, sigma_z=cz,
                source=position_source,
                is_measured_uncertainty=is_meas
            )
        )
        
    res, stats = robust_position_alignment(centers, gnss_priors, inlier_threshold=2.0)
    
    if res is None or stats["used_priors"] < 3:
        return {
            "valid": False,
            "metric_state": MetricState.RELATIVE.value,
            "reason": "Cannot determine robust visual-to-GPS alignment.",
            "scale": 1.0,
            "rotation": np.eye(3).tolist(),
            "translation": np.zeros(3).tolist(),
            "origin": origin.tolist(),
            "epsg": epsg,
            "coordinate_system": "UTM",
            "rmse_m": None,
        }

    return {
        "valid": True,
        "metric_state": MetricState.GEOREFERENCED_METRIC.value,
        "scale": float(res["s"]),
        "rotation": res["R"].tolist(),
        "translation": res["t"].tolist(),
        "origin": origin.tolist(),
        "epsg": epsg,
        "coordinate_system": "UTM",
        "rmse_m": stats["rmse"],
        "alignment_inliers": stats["used_priors"],
        "alignment_samples": stats["total_priors"],
        "gps_residuals_m": [],
        "rtk_used": rtk_used,
        "barometer_used": baro_used,
        "checkpoint_rmse_3d": None,
        "position_source": position_source
    }


def transform(points, geo):
    if geo["metric_state"] != MetricState.RELATIVE.value:
        s = geo["scale"]
        r = np.array(geo["rotation"])
        t = np.array(geo["translation"])
        return s * points @ r.T + t
    return points
