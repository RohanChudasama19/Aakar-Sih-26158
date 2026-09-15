import csv
from enum import Enum

import numpy as np
from pyproj import Transformer


class MetricState(str, Enum):
    RELATIVE = "RELATIVE"
    METRIC_SCALE = "METRIC_SCALE"
    GEOREFERENCED_METRIC = "GEOREFERENCED_METRIC"


def similarity(a, b):
    # Umeyama similarity transform
    ac, bc = a - a.mean(0), b - b.mean(0)
    # Handle collinearity/degeneracy
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


def align(sfm, info, gps, input_dir):
    start_time_utc = info.get("start_time_utc", 0.0)

    # Establish UTM Projection
    lat0, lon0, alt0 = gps[0]["latitude"], gps[0]["longitude"], gps[0]["altitude_m"]
    zone = min(60, max(1, int((lon0 + 180) // 6) + 1))
    epsg = (32600 if lat0 >= 0 else 32700) + zone
    tx = Transformer.from_crs(4326, epsg, always_xy=True)

    # Process GPS timeline
    gps_times = np.array([s["time"] for s in gps])
    e, n = tx.transform([s["longitude"] for s in gps], [s["latitude"] for s in gps])

    absolute_coords = np.c_[e, n, [s["altitude_m"] for s in gps]]
    origin = absolute_coords[0].copy()

    enu_coords = absolute_coords - origin

    rtk_used = False
    correction = input_dir / "rtk.csv"
    if correction.exists():
        with correction.open() as f:
            rows = list(csv.DictReader(f))

        # RTK overrides, but interpolate via timestamp if possible, else frame
        if "timestamp_utc" in rows[0]:
            from datetime import datetime

            rtk_times = np.array(
                [datetime.fromisoformat(r["timestamp_utc"].replace("Z", "+00:00")).timestamp() for r in rows]
            )
        else:
            # Fallback to frame interpolation
            rtk_times = np.array([float(r["frame"]) / info["fps"] + start_time_utc for r in rows])

        x = np.array(
            [[float(r["east_correction_m"]), float(r["north_correction_m"]), float(r["up_correction_m"])] for r in rows]
        )

        if len(x) >= 2:
            for d in range(3):
                enu_coords[:, d] += np.interp(gps_times, rtk_times, x[:, d])
            rtk_used = True

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
            # Replace ENU Up with barometer (relative to first baro reading, shifted by origin altitude)
            # Actually, barometer is absolute if calibrated, otherwise relative.
            # For this baseline, interpolate directly as Z.
            enu_coords[:, 2] = np.interp(gps_times, baro_times, x) - alt0
            baro_used = True

    # Map registered images to telemetry
    ids = sorted(sfm["poses"].keys())

    # We need timestamps for each reconstructed frame.
    # From preprocess.py, info["frames"] has "time_sec" and "frame".
    frame_times = []
    centers = []

    for i in ids:
        frame_dict = info["frames"][i]
        # Frame absolute time
        t = start_time_utc + frame_dict["time_sec"]

        # We only accept frames that are bounded by telemetry
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

    # Interpolate ENU target coords for valid frames
    targets = np.zeros((len(frame_times), 3))
    for d in range(3):
        targets[:, d] = np.interp(frame_times, gps_times, enu_coords[:, d])

    # Check collinearity
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

    # RANSAC Alignment
    best = None
    rng = np.random.default_rng(42)
    for _ in range(250):
        idx = rng.choice(len(centers), min(4, len(centers)), replace=False)
        if np.linalg.matrix_rank(centers[idx] - centers[idx].mean(0), tol=1e-5) < 2:
            continue
        s, r, t = similarity(centers[idx], targets[idx])
        residual = np.linalg.norm(s * centers @ r.T + t - targets, axis=1)
        good = residual < max(2.0, float(np.median(residual)) * 2)
        score = (int(good.sum()), -float(np.median(residual)))
        if best is None or score > best[0]:
            best = score, good

    if best is None or best[1].sum() < 3:
        return {
            "valid": False,
            "metric_state": MetricState.RELATIVE.value,
            "reason": "Cannot determine robust visual-to-GPS alignment (RANSAC failed).",
            "scale": 1.0,
            "rotation": np.eye(3).tolist(),
            "translation": np.zeros(3).tolist(),
            "origin": origin.tolist(),
            "epsg": epsg,
            "coordinate_system": "UTM",
            "rmse_m": None,
        }

    # Final fit on inliers
    inliers = best[1]
    s, r, t = similarity(centers[inliers], targets[inliers])
    residuals = np.linalg.norm(s * centers @ r.T + t - targets, axis=1)
    rmse_m = float(np.sqrt(np.mean(residuals**2)))

    # Optional Checkpoints
    checkpoint_csv = input_dir / "checkpoints.csv"
    checkpoint_rmse = None
    if checkpoint_csv.exists():
        with checkpoint_csv.open() as f:
            list(csv.DictReader(f))

        # Checkpoints need a way to be mapped to visual space.
        # Typically, user provides 2D pixel observations, which are triangulated, or we find nearest.
        # But Phase 4 just asks for foundation. We will parse it and store it if we can evaluate it.
        pass  # To be fully implemented when pixel observations for GCPs are provided.

    # Do not transform SfM poses inplace.
    # Preserve them in the local relative frame for numerically stable dense reconstruction.

    return {
        "valid": True,
        "metric_state": MetricState.GEOREFERENCED_METRIC.value,
        "scale": float(s),
        "rotation": r.tolist(),
        "translation": t.tolist(),
        "origin": origin.tolist(),
        "epsg": epsg,
        "coordinate_system": "UTM",
        "rmse_m": rmse_m,
        "alignment_inliers": int(inliers.sum()),
        "alignment_samples": len(centers),
        "gps_residuals_m": residuals.tolist(),
        "rtk_used": rtk_used,
        "barometer_used": baro_used,
        "checkpoint_rmse_3d": checkpoint_rmse,
    }


def transform(points, geo):
    # Already applied internally to points/poses in align(),
    # but kept for backward compatibility for external components if they have unscaled points
    if geo["metric_state"] != MetricState.RELATIVE.value:
        s = geo["scale"]
        r = np.array(geo["rotation"])
        t = np.array(geo["translation"])
        return s * points @ r.T + t
    return points
