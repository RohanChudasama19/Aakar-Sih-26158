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


def intrinsics(meta: Dict[str, Any], width: int, height: int, override: Optional[Dict[str, Any]] = None) -> np.ndarray:
    x = override or meta["camera_intrinsics"]
    if "fx" in x:
        sx, sy = width / float(x["image_width_px"]), height / float(x["image_height_px"])
        k = np.array(
            [[float(x["fx"]) * sx, 0, float(x["cx"]) * sx], [0, float(x["fy"]) * sy, float(x["cy"]) * sy], [0, 0, 1.0]]
        )
    else:
        f = float(x["focal_length_mm"])
        k = np.array(
            [
                [f / float(x["sensor_width_mm"]) * width, 0, width / 2],
                [0, f / float(x["sensor_height_mm"]) * height, height / 2],
                [0, 0, 1.0],
            ]
        )
    if not np.isfinite(k).all() or k[0, 0] <= 0 or k[1, 1] <= 0:
        raise ValueError("Invalid camera intrinsics")
    return k
