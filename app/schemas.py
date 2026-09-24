import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from .camera import CalibrationSource, CalibrationState, CameraModel, CameraModelType

GPS_COLUMNS_OPTIONAL = [
    "frame",
    "compass_heading_deg",
    "gimbal_pitch_deg",
    "gimbal_yaw_deg",
    "speed_mps",
    "satellites",
    "rtk_quality",
    "heading",
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


def telemetry(path: Path) -> List[Dict[str, Any]]:
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        
        # Check required fields (support timestamp or timestamp_utc)
        has_ts = "timestamp_utc" in fields or "timestamp" in fields
        has_lat = "latitude" in fields
        has_lon = "longitude" in fields
        has_alt = "altitude_m" in fields or "altitude" in fields
        
        if not (has_ts and has_lat and has_lon and has_alt):
            raise ValueError("GPS CSV requires core columns: timestamp, latitude, longitude, altitude")
            
        ts_col = "timestamp_utc" if "timestamp_utc" in fields else "timestamp"
        alt_col = "altitude_m" if "altitude_m" in fields else "altitude"
            
        rows = []
        for r in reader:
            ts_str = r[ts_col].replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(ts_str)
                if dt.tzinfo is None:
                    raise ValueError("Telemetry timestamps must include UTC timezone")
                ts_val = dt.timestamp()
            except ValueError:
                # Fallback to direct float parsing if it's already a unix timestamp
                ts_val = float(ts_str)
                
            x = {}
            for k in fields:
                if k not in (ts_col,):
                    try:
                        x[k] = float(r[k])
                    except ValueError:
                        x[k] = r[k]
                        
            # Normalize altitude key to altitude_m for downstream compatibility
            if "altitude_m" not in x and "altitude" in x:
                x["altitude_m"] = x["altitude"]
                
            # Normalize frame key to avoid KeyError downstream
            if "frame" not in x:
                x["frame"] = 0
            elif x["frame"] < 0 or x["frame"] != int(x["frame"]):
                raise ValueError("GPS frame must be a nonnegative integer")
                
            x["time"] = ts_val
            
            # The downstream checks require validity across core fields, 
            # we just ensure they aren't completely degenerate
            if (
                abs(x["latitude"]) > 90
                or abs(x["longitude"]) > 180
                or x.get("altitude_m", 0) < -1000
                or x.get("altitude_m", 0) > 20000
            ):
                raise ValueError(f"Invalid GPS bounds at frame {x.get('frame', 0)}")
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


def intrinsics(meta: Dict[str, Any], width: int, height: int, override: Optional[Dict[str, Any]] = None) -> CameraModel:
    if override:
        source = CalibrationSource.PROVIDED_CALIBRATION
        state = CalibrationState.CALIBRATED
        x = override
    elif "camera_intrinsics" in meta:
        source = CalibrationSource.PROVIDED_CALIBRATION
        state = CalibrationState.CALIBRATED
        x = meta["camera_intrinsics"]
    else:
        x = {}

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
        # Exif / Sensor derived fallback is fundamentally untrustworthy unless strictly validated.
        # Mixing 35mm-equivalent focal lengths with physical sensor sizes leads to massive errors.
        # We will initialize with a generic prior and let SIMPLE_RADIAL refine it.
        source = CalibrationSource.METADATA_DERIVED
        state = CalibrationState.ESTIMATED
        
        orig_w = int(x.get("image_width_px", width))
        orig_h = int(x.get("image_height_px", height))

        # Reasonable prior for wide-angle UAV cameras: 75-85 deg FOV
        # fx roughly equals 0.85 * width.
        focal_guess = 0.85 * orig_w
        
        cam = CameraModel(
            model_type=CameraModelType.SIMPLE_RADIAL,
            width=orig_w,
            height=orig_h,
            fx=focal_guess,
            fy=focal_guess,
            cx=orig_w / 2.0,
            cy=orig_h / 2.0,
            distortion=[0.0],
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
