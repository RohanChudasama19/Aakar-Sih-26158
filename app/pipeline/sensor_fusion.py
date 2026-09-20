import csv
import json
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class LeverArmStatus(str, Enum):
    APPLIED = "APPLIED"
    BLOCKED_FRAME_UNKNOWN = "LEVER_ARM_BLOCKED_FRAME_UNKNOWN"
    NOT_PROVIDED = "NOT_PROVIDED"


@dataclass
class LeverArmConfig:
    translation_vector: Tuple[float, float, float]
    source_frame: str
    destination_frame: str
    units: str = "m"
    status: LeverArmStatus = LeverArmStatus.NOT_PROVIDED


class FusionStatus(str, Enum):
    DISABLED = "DISABLED"
    AVAILABLE = "AVAILABLE"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    BLOCKED_FRAME_UNKNOWN = "BLOCKED_FRAME_UNKNOWN"
    BLOCKED_EXTRINSIC_MISSING = "BLOCKED_EXTRINSIC_MISSING"
    MISSING_DATA = "MISSING_DATA"


class GNSSQuality(str, Enum):
    RTK_FIXED = "RTK_FIXED"
    RTK_FLOAT = "RTK_FLOAT"
    PPK_FIXED = "PPK_FIXED"
    PPK_FLOAT = "PPK_FLOAT"
    DGPS = "DGPS"
    GNSS_SINGLE = "GNSS_SINGLE"
    UNKNOWN = "UNKNOWN"


DEFAULT_SIGMA = {
    GNSSQuality.RTK_FIXED: 0.02,
    GNSSQuality.RTK_FLOAT: 0.2,
    GNSSQuality.PPK_FIXED: 0.02,
    GNSSQuality.PPK_FLOAT: 0.2,
    GNSSQuality.DGPS: 0.5,
    GNSSQuality.GNSS_SINGLE: 2.5,
    GNSSQuality.UNKNOWN: 5.0,
}


@dataclass
class PositionPrior:
    timestamp: float
    x: float
    y: float
    z: float
    quality: GNSSQuality
    sigma_x: float
    sigma_y: float
    sigma_z: float
    source: str
    satellite_count: Optional[int] = None
    is_measured_uncertainty: bool = False


def parse_gnss_quality(q_str: str) -> GNSSQuality:
    if not q_str:
        return GNSSQuality.UNKNOWN
    q = str(q_str).upper()
    for enum_val in GNSSQuality:
        if enum_val.value == q:
            return enum_val
    return GNSSQuality.UNKNOWN


def compute_sigma(
    quality: GNSSQuality, sig_x: Optional[float], sig_y: Optional[float], sig_z: Optional[float]
) -> Tuple[float, float, float, bool]:
    base = DEFAULT_SIGMA.get(quality, 5.0)

    def _safe_sig(val, fallback):
        if val is None or math.isnan(val) or val <= 0:
            return fallback
        return max(0.001, val)

    sx = _safe_sig(sig_x, base)
    sy = _safe_sig(sig_y, base)
    sz = _safe_sig(sig_z, base * 1.5)
    is_meas = (
        (sig_x is not None and sig_x > 0) and (sig_y is not None and sig_y > 0) and (sig_z is not None and sig_z > 0)
    )
    return sx, sy, sz, is_meas


def pressure_to_relative_altitude(pressure_hpa: float, ref_pressure_hpa: float, temp_c: float = 15.0) -> float:
    if pressure_hpa <= 0 or ref_pressure_hpa <= 0:
        return 0.0
    T0 = temp_c + 273.15
    g = 9.80665
    M = 0.0289644
    R = 8.3144598
    return float((R * T0) / (g * M) * math.log(ref_pressure_hpa / pressure_hpa))


def check_orientation_fusion_safety(meta: dict) -> FusionStatus:
    if meta.get("imu_orientation_convention") == "UNKNOWN":
        return FusionStatus.BLOCKED_FRAME_UNKNOWN
    if meta.get("camera_imu_extrinsics", "NOT_AVAILABLE") == "NOT_AVAILABLE":
        return FusionStatus.BLOCKED_EXTRINSIC_MISSING
    return FusionStatus.AVAILABLE


def fuse_orientation():
    raise ValueError("ORIENTATION_FUSION_BLOCKED")


def align_trajectories_umeyama(
    src: np.ndarray, dst: np.ndarray, weights: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, float]:
    assert src.shape == dst.shape
    assert src.shape[1] == 3

    W = np.sum(weights)
    if W == 0:
        return np.eye(3), np.zeros(3), 1.0

    src_mean = np.sum(src * weights[:, None], axis=0) / W
    dst_mean = np.sum(dst * weights[:, None], axis=0) / W

    src_demean = src - src_mean
    dst_demean = dst - dst_mean

    sigma_src = np.sum(weights * np.sum(src_demean**2, axis=1)) / W

    cov = (dst_demean * weights[:, None]).T @ src_demean / W

    U, D, Vt = np.linalg.svd(cov)
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[2, 2] = -1

    R = U @ S @ Vt

    s = 1.0
    if sigma_src > 1e-8:
        s = np.trace(np.diag(D) @ S) / sigma_src

    t = dst_mean - s * (R @ src_mean)

    return R, t, s


def robust_position_alignment(
    visual_positions: np.ndarray, gnss_priors: List[PositionPrior], inlier_threshold: float = 2.0
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    if len(visual_positions) < 3 or len(visual_positions) != len(gnss_priors):
        return None, {"error": "Insufficient or mismatched points"}

    dst = np.array([[p.x, p.y, p.z] for p in gnss_priors])
    src = visual_positions

    sigmas = np.array([(p.sigma_x + p.sigma_y + p.sigma_z) / 3.0 for p in gnss_priors])
    weights = 1.0 / (sigmas**2)
    weights = np.clip(weights, 1e-4, 1e4)

    n = len(src)
    best_inliers = np.zeros(n, dtype=bool)
    best_num = 0

    # Basic RANSAC
    import random

    np.random.seed(42)
    random.seed(42)
    iterations = min(100, max(10, n * 2))

    for _ in range(iterations):
        if n < 3:
            break
        idx = random.sample(range(n), 3)
        R_tmp, t_tmp, s_tmp = align_trajectories_umeyama(src[idx], dst[idx], np.ones(3))
        err = np.linalg.norm(s_tmp * (src @ R_tmp.T) + t_tmp - dst, axis=1)
        inliers = err < inlier_threshold
        num = np.sum(inliers)
        if num > best_num:
            best_num = num
            best_inliers = inliers

    if best_num < 3:
        best_inliers = np.ones(n, dtype=bool)  # Fallback to all

    weights_inlier = weights * best_inliers
    R, t, s = align_trajectories_umeyama(src, dst, weights_inlier)
    transformed_src = s * (src @ R.T) + t
    errors = np.linalg.norm(transformed_src - dst, axis=1)

    final_inliers = errors < inlier_threshold
    num_inliers = np.sum(final_inliers)

    stats = {
        "total_priors": len(gnss_priors),
        "used_priors": int(num_inliers),
        "rejected_priors": len(gnss_priors) - int(num_inliers),
        "rmse": float(np.sqrt(np.mean(errors[final_inliers] ** 2))) if num_inliers > 0 else 0.0,
        "median_residual": float(np.median(errors[final_inliers])) if num_inliers > 0 else 0.0,
        "max_residual": float(np.max(errors[final_inliers])) if num_inliers > 0 else 0.0,
    }

    return {"R": R, "t": t, "s": s}, stats


class PhaseE1Fusion:
    def __init__(self, metadata: dict):
        self.metadata = metadata
        self.gnss_priors: List[PositionPrior] = []
        self.baro_ref_pressure: Optional[float] = None
        self.orientation_status = check_orientation_fusion_safety(metadata)

        self.report = {
            "fusion_status": {
                "gnss": FusionStatus.MISSING_DATA.value,
                "barometer": FusionStatus.MISSING_DATA.value,
                "accel_magnitude": FusionStatus.MISSING_DATA.value,
                "gyro_magnitude": FusionStatus.MISSING_DATA.value,
                "orientation": self.orientation_status.value,
            },
            "gnss_statistics": {},
            "barometer_statistics": {},
            "motion_quality_statistics": {},
        }
        self.motion_risk_frame_count = 0
        self.baro_alts: List[float] = []

    def add_gnss_measurement(
        self,
        ts: float,
        x: float,
        y: float,
        z: float,
        q_str: str = "",
        sx: Optional[float] = None,
        sy: Optional[float] = None,
        sz: Optional[float] = None,
        sat_count: Optional[int] = None,
    ):
        q = parse_gnss_quality(q_str)
        cx, cy, cz, is_meas = compute_sigma(q, sx, sy, sz)
        self.gnss_priors.append(PositionPrior(ts, x, y, z, q, cx, cy, cz, "gnss", sat_count, is_meas))
        self.report["fusion_status"]["gnss"] = FusionStatus.ACTIVE.value

    def process_frame(self, frame_data: dict) -> dict:
        mq: Dict[str, Any] = {
            "motion_quality_score": 1.0,
            "rapid_rotation": False,
            "high_acceleration": False,
            "blur_risk": "LOW",
            "frame_index": frame_data.get("frame_index", -1),
        }

        if "accel_x" in frame_data and frame_data["accel_x"] != "":
            ax, ay, az = float(frame_data["accel_x"]), float(frame_data["accel_y"]), float(frame_data["accel_z"])
            a_mag = math.sqrt(ax**2 + ay**2 + az**2)
            self.report["fusion_status"]["accel_magnitude"] = FusionStatus.ACTIVE.value

            a_dev = abs(a_mag - 9.81)
            if a_dev > 3.0:
                mq["high_acceleration"] = True
                mq["motion_quality_score"] *= max(0.1, 1.0 - a_dev / 10.0)

        if "gyro_x" in frame_data and frame_data["gyro_x"] != "":
            gx, gy, gz = float(frame_data["gyro_x"]), float(frame_data["gyro_y"]), float(frame_data["gyro_z"])
            g_mag = math.sqrt(gx**2 + gy**2 + gz**2)
            self.report["fusion_status"]["gyro_magnitude"] = FusionStatus.ACTIVE.value

            if g_mag > 1.0:
                mq["rapid_rotation"] = True
                mq["blur_risk"] = "HIGH" if g_mag > 2.0 else "MEDIUM"
                mq["motion_quality_score"] *= max(0.1, 1.0 - g_mag / 5.0)

        if "pressure" in frame_data and frame_data["pressure"] != "":
            p = float(frame_data["pressure"])
            if self.baro_ref_pressure is None:
                self.baro_ref_pressure = p
            rel_alt = pressure_to_relative_altitude(p, self.baro_ref_pressure)
            mq["relative_altitude_m"] = rel_alt
            self.baro_alts.append(rel_alt)
            self.report["fusion_status"]["barometer"] = FusionStatus.ACTIVE.value

        mq["motion_quality_score"] = round(mq["motion_quality_score"], 3)
        if mq["motion_quality_score"] < 0.7 or mq["rapid_rotation"] or mq["high_acceleration"]:
            self.motion_risk_frame_count += 1

        return mq

    def finalize(self):
        # GNSS stats
        if self.gnss_priors:
            self.report["gnss_statistics"]["total_priors_extracted"] = len(self.gnss_priors)

        # Baro stats
        if self.baro_alts:
            self.report["barometer_statistics"]["altitude_range_m"] = [
                float(min(self.baro_alts)),
                float(max(self.baro_alts)),
            ]
            self.report["barometer_statistics"]["sample_count"] = len(self.baro_alts)

            # Simple bias/drift against GNSS Z
            if self.gnss_priors and len(self.gnss_priors) == len(self.baro_alts):
                gnss_z = np.array([p.z for p in self.gnss_priors])
                baro_z = np.array(self.baro_alts)
                # We fit GNSS_Z = Baro_Z + bias + drift * t
                # Or just bias = mean(GNSS_Z - Baro_Z)
                diff = gnss_z - baro_z
                ts = np.array([p.timestamp for p in self.gnss_priors])
                ts -= ts[0]  # relative time

                if len(ts) > 2 and ts[-1] > 0:
                    A = np.vstack([np.ones_like(ts), ts]).T
                    bias, drift = np.linalg.lstsq(A, diff, rcond=None)[0]
                    res = diff - (bias + drift * ts)
                    self.report["barometer_statistics"]["initial_bias"] = float(bias)
                    self.report["barometer_statistics"]["drift_estimate"] = float(drift)
                    self.report["barometer_statistics"]["residual_trend"] = float(np.std(res))
                else:
                    self.report["barometer_statistics"]["initial_bias"] = float(np.mean(diff))
                    self.report["barometer_statistics"]["drift_estimate"] = 0.0
                    self.report["barometer_statistics"]["residual_trend"] = 0.0

        self.report["motion_quality_statistics"]["motion_risk_frame_count"] = self.motion_risk_frame_count


def run_phase_e1_audit(mission_dir: Path):
    telemetry_dir = mission_dir / "telemetry"

    meta = {}
    if (telemetry_dir / "flight_metadata.json").exists():
        with open(telemetry_dir / "flight_metadata.json") as f:
            meta = json.load(f)

    fusion = PhaseE1Fusion(meta)

    sync_csv = telemetry_dir / "synchronized_telemetry.csv"
    if sync_csv.exists():
        with open(sync_csv) as f:
            reader = csv.DictReader(f)
            for r in reader:
                # Add GNSS
                if r.get("lat") and r.get("lon") and r.get("alt"):
                    # For metric conversion, time_sync already uses geodetic.
                    # We just use lat/lon/alt as proxy if Cartesian not available, but real system projects to ENU/UTM.
                    # We'll just pass them through to record the count.
                    fusion.add_gnss_measurement(
                        ts=float(r["frame_timestamp"]),
                        x=float(r["lon"]),
                        y=float(r["lat"]),
                        z=float(r["alt"]),
                        q_str=r.get("gps_status", "UNKNOWN"),
                    )
                fusion.process_frame(r)

    fusion.finalize()

    with open(telemetry_dir / "sensor_fusion_report.json", "w") as f:
        json.dump(fusion.report, f, indent=2)

    return fusion.report


if __name__ == "__main__":
    import sys

    run_phase_e1_audit(Path(sys.argv[1]))
