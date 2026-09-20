import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

from app.pipeline.sensor_fusion import align_trajectories_umeyama


class ControlRole(str, Enum):
    CONTROL = "CONTROL"
    CHECKPOINT = "CHECKPOINT"


class VerticalDatum(str, Enum):
    ELLIPSOIDAL = "ELLIPSOIDAL"
    ORTHOMETRIC = "ORTHOMETRIC"
    LOCAL = "LOCAL"
    UNKNOWN = "UNKNOWN"


@dataclass
class GroundControlPoint:
    checkpoint_id: str
    latitude: float
    longitude: float
    elevation: float
    role: ControlRole
    recon_x: float
    recon_y: float
    recon_z: float
    vertical_datum: VerticalDatum = VerticalDatum.UNKNOWN
    reference_accuracy_horizontal_m: float = 0.05
    reference_accuracy_vertical_m: float = 0.1
    survey_method: str = "UNKNOWN"


class GeometryQuality(str, Enum):
    GOOD = "CONTROL_GEOMETRY_GOOD"
    WEAK = "CONTROL_GEOMETRY_WEAK"
    INVALID = "CONTROL_GEOMETRY_INVALID"


def check_control_geometry(controls: List[GroundControlPoint]) -> Tuple[GeometryQuality, List[str]]:
    warnings = []
    if len(controls) < 4:
        warnings.append(f"Insufficient control points: {len(controls)} < 4")
        return GeometryQuality.INVALID, warnings

    coords = np.array([[c.latitude, c.longitude, c.elevation] for c in controls])
    lat_mean = np.mean(coords[:, 0])
    lon_scale = np.cos(np.radians(lat_mean))

    x = (coords[:, 1] - np.mean(coords[:, 1])) * 111000 * lon_scale
    y = (coords[:, 0] - np.mean(coords[:, 0])) * 111000
    z = coords[:, 2] - np.mean(coords[:, 2])

    local_pts = np.column_stack((x, y, z))

    cov = np.cov(local_pts, rowvar=False)
    eigvals = np.linalg.eigvalsh(cov)

    if eigvals[-1] == 0 or (eigvals[0] / eigvals[-1]) < 1e-6:
        warnings.append("Control points are nearly collinear or coplanar.")
        return GeometryQuality.WEAK, warnings

    elev_range = float(np.max(z) - np.min(z))
    if elev_range < 0.5:
        warnings.append("Insufficient elevation diversity (<0.5m range).")

    dists = []
    for i in range(len(local_pts)):
        other_pts = np.delete(local_pts, i, axis=0)
        min_dist = float(np.min(np.linalg.norm(other_pts - local_pts[i], axis=1)))
        dists.append(min_dist)

    if np.min(dists) < 0.1:
        warnings.append("Control points are tightly clustered.")

    if len(warnings) > 0:
        return GeometryQuality.WEAK, warnings

    return GeometryQuality.GOOD, []


def fit_control_alignment(controls: List[GroundControlPoint], out_dir: Path, target_epsg: int) -> Dict[str, Any]:
    active_controls = [c for c in controls if c.role == ControlRole.CONTROL]
    checkpoints = [c for c in controls if c.role == ControlRole.CHECKPOINT]

    quality, warnings = check_control_geometry(active_controls)

    if quality == GeometryQuality.INVALID:
        raise ValueError(" ".join(warnings))

    import pyproj

    tx = pyproj.Transformer.from_crs(4326, target_epsg, always_xy=True)

    src_list = []
    dst_list = []
    weights_list = []
    controls_used = []

    vertical_datum_state = active_controls[0].vertical_datum if active_controls else VerticalDatum.UNKNOWN
    for c in active_controls:
        if c.vertical_datum != vertical_datum_state:
            vertical_datum_state = VerticalDatum.UNKNOWN

    force_horizontal = vertical_datum_state == VerticalDatum.UNKNOWN

    for c in active_controls:
        e, n = tx.transform(c.longitude, c.latitude)
        dst_list.append([e, n, c.elevation if not force_horizontal else 0.0])
        src_list.append([c.recon_x, c.recon_y, c.recon_z if not force_horizontal else 0.0])
        w = 1.0 / (
            c.reference_accuracy_horizontal_m**2
            + (c.reference_accuracy_vertical_m**2 if not force_horizontal else 0.0001)
        )
        weights_list.append(w)
        controls_used.append(c)

    src = np.array(src_list)
    dst = np.array(dst_list)
    weights = np.array(weights_list)

    if len(src) < 3:
        raise ValueError("Need at least 3 control points to fit transform.")

    best_inliers = np.ones(len(src), dtype=bool)
    best_num = -1
    inlier_threshold = 0.5

    rng = np.random.default_rng(42)
    for _ in range(250):
        idx = rng.choice(len(src), min(4, len(src)), replace=False)
        if np.linalg.matrix_rank(src[idx] - src[idx].mean(0), tol=1e-5) < 2:
            continue

        R_tmp, t_tmp, s_tmp = align_trajectories_umeyama(src[idx], dst[idx], np.ones(len(idx)))
        if np.any(np.isnan(R_tmp)):
            continue

        err = np.linalg.norm(s_tmp * (src @ R_tmp.T) + t_tmp - dst, axis=1)
        inliers = err < inlier_threshold
        num = np.sum(inliers)
        if num > best_num:
            best_num = num
            best_inliers = inliers

    if best_num < 3:
        best_inliers = np.ones(len(src), dtype=bool)

    w_inlier = weights * best_inliers
    R, t, s = align_trajectories_umeyama(src, dst, w_inlier)

    transformed_src = s * (src @ R.T) + t
    residuals = np.linalg.norm(transformed_src - dst, axis=1)

    res_details = []
    for i, c in enumerate(controls_used):
        res_details.append({"id": c.checkpoint_id, "used": bool(best_inliers[i]), "residual_m": float(residuals[i])})

    inliers_arr = residuals[best_inliers]
    rmse = float(np.sqrt(np.mean(inliers_arr**2))) if len(inliers_arr) > 0 else 0.0

    rep = {
        "control_count": len(controls_used),
        "checkpoint_count": len(checkpoints),
        "transform": {"scale": float(s), "rotation": R.tolist(), "translation": t.tolist()},
        "control_residuals": res_details,
        "robust_inliers": int(np.sum(best_inliers)),
        "rejected_controls": len(controls_used) - int(np.sum(best_inliers)),
        "CONTROL_FIT_RMSE": rmse,
        "geometry_quality": quality.value,
        "vertical_datum_status": vertical_datum_state.value,
        "mode": "GCP_HORIZONTAL_ONLY" if force_horizontal else "GCP_3D",
        "warnings": warnings,
    }

    with open(out_dir / "gcp_alignment_report.json", "w") as f:
        json.dump(rep, f, indent=2)

    return rep
