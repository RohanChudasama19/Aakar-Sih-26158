import csv
import json
from datetime import datetime

import numpy as np

GPS_COLUMNS = [
    "timestamp_utc",
    "frame",
    "latitude",
    "longitude",
    "altitude_m",
    "compass_heading_deg",
    "gimbal_pitch_deg",
    "gimbal_yaw_deg",
    "speed_mps",
    "satellites",
]
META_FIELDS = [
    "mission_name",
    "drone_model",
    "camera_sensor",
    "video_file",
    "video_resolution",
    "video_fps",
    "video_duration_sec",
    "home_point",
    "start_time_utc",
    "end_time_utc",
    "camera_intrinsics",
]


from pathlib import Path
from typing import Any, Dict, List, Optional


def telemetry(path: Path) -> List[Dict[str, Any]]:
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        if not set(GPS_COLUMNS).issubset(reader.fieldnames or []):
            raise ValueError("GPS CSV requires columns: " + ", ".join(GPS_COLUMNS))
        rows = []
        for r in reader:
            dt = datetime.fromisoformat(r["timestamp_utc"].replace("Z", "+00:00"))
            if dt.tzinfo is None:
                raise ValueError("Telemetry timestamps must include UTC timezone")
            x = {k: float(r[k]) for k in GPS_COLUMNS if k != "timestamp_utc"}
            x["time"] = dt.timestamp()
            if (
                not np.isfinite(list(x.values())).all()
                or not -90 <= x["latitude"] <= 90
                or not -180 <= x["longitude"] <= 180
            ):
                raise ValueError("GPS contains invalid numeric values")
            if x["frame"] < 0 or x["frame"] != int(x["frame"]):
                raise ValueError("GPS frame must be a nonnegative integer")
            rows.append(x)
    if len(rows) < 3:
        raise ValueError("At least three telemetry samples are required")
    if any(b["time"] <= a["time"] or b["frame"] <= a["frame"] for a, b in zip(rows, rows[1:])):
        raise ValueError("GPS timestamps and frames must be strictly increasing")
    return rows


def metadata(path: Path) -> Dict[str, Any]:
    m = json.loads(path.read_text())
    missing = set(META_FIELDS) - m.keys()
    if missing:
        raise ValueError("Flight metadata missing: " + ", ".join(sorted(missing)))
    for k in ["video_fps", "video_duration_sec"]:
        if not np.isfinite(float(m[k])) or float(m[k]) <= 0:
            raise ValueError(k + " must be positive")
    for k in ["latitude", "longitude", "altitude_m"]:
        if not np.isfinite(float(m["home_point"][k])):
            raise ValueError("Invalid home_point")
    start = datetime.fromisoformat(m["start_time_utc"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(m["end_time_utc"].replace("Z", "+00:00"))
    if start.tzinfo is None or end.tzinfo is None or end <= start:
        raise ValueError("Flight times must be timezone-aware and increasing")
    return m


from .camera import CalibrationSource, CalibrationState, CameraModel, CameraModelType


def intrinsics(meta: Dict[str, Any], width: int, height: int, override: Optional[Dict[str, Any]] = None) -> CameraModel:
    if override:
        source = CalibrationSource.PROVIDED_CALIBRATION
        state = CalibrationState.CALIBRATED
        x = override
    elif "camera_intrinsics" in meta and meta["camera_intrinsics"]:
        source = CalibrationSource.PROVIDED_CALIBRATION
        state = CalibrationState.CALIBRATED
        x = meta["camera_intrinsics"]
    else:
        # Should not reach here if schemas are validated strictly, but just in case
        raise ValueError("Missing camera_intrinsics in metadata")

    if "fx" in x:
        # Already formatted somewhat like our schema
        cam = CameraModel(
            model_type=CameraModelType(x.get("camera_model", "PINHOLE")),
            width=int(x.get("image_width_px", x.get("image_width", width))),
            height=int(x.get("image_height_px", x.get("image_height", height))),
            fx=float(x["fx"]),
            fy=float(x.get("fy", x["fx"])),
            cx=float(x.get("cx", width / 2.0)),
            cy=float(x.get("cy", height / 2.0)),
            distortion=[float(v) for v in x.get("distortion", [])],
            source=source,
            state=state,
            original_width=int(x.get("image_width_px", x.get("image_width", width))),
            original_height=int(x.get("image_height_px", x.get("image_height", height))),
        )
    else:
        # Exif / Sensor derived fallback
        source = CalibrationSource.METADATA_DERIVED
        state = CalibrationState.ESTIMATED
        f = float(x["focal_length_mm"])
        sw = float(x.get("sensor_width_mm", 36.0))  # Fallback to full frame equivalent if missing
        sh = float(x.get("sensor_height_mm", 24.0))

        orig_w = int(x.get("image_width_px", width))
        orig_h = int(x.get("image_height_px", height))

        cam = CameraModel(
            model_type=CameraModelType.PINHOLE,
            width=orig_w,
            height=orig_h,
            fx=f / sw * orig_w,
            fy=f / sh * orig_h,
            cx=orig_w / 2.0,
            cy=orig_h / 2.0,
            source=source,
            state=state,
            original_width=orig_w,
            original_height=orig_h,
        )

    if not np.isfinite([cam.fx, cam.fy, cam.cx, cam.cy]).all() or cam.fx <= 0 or cam.fy <= 0:
        raise ValueError("Invalid camera intrinsics")

    # If the processing resolution is different, scale the model explicitly
    if cam.width != width or cam.height != height:
        cam = cam.scale(width, height)

    return cam
