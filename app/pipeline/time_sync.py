import csv
import json
import math
from pathlib import Path
from typing import Any, List, Optional, Tuple

# Geodetic to Cartesian constants (WGS84)
A = 6378137.0
E2 = 0.00669437999014


def geodetic_to_ecef(lat: float, lon: float, alt: float) -> Tuple[float, float, float]:
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    n = A / math.sqrt(1 - E2 * math.sin(lat_rad) ** 2)
    x = (n + alt) * math.cos(lat_rad) * math.cos(lon_rad)
    y = (n + alt) * math.cos(lat_rad) * math.sin(lon_rad)
    z = (n * (1 - E2) + alt) * math.sin(lat_rad)
    return x, y, z


def ecef_to_geodetic(x: float, y: float, z: float) -> Tuple[float, float, float]:
    # Bowring's approximation
    p = math.sqrt(x**2 + y**2)
    if p < 1e-10:
        return (90.0 if z > 0 else -90.0, 0.0, z - A * math.sqrt(1 - E2))
    lon = math.atan2(y, x)
    lat = math.atan2(z, p * (1 - E2))
    for _ in range(5):
        n = A / math.sqrt(1 - E2 * math.sin(lat) ** 2)
        alt = p / math.cos(lat) - n
        lat = math.atan2(z, p * (1 - E2 * n / (n + alt)))
    return math.degrees(lat), math.degrees(lon), alt


def quaternion_slerp(q1, q2, t):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    dot = w1 * w2 + x1 * x2 + y1 * y2 + z1 * z2
    if dot < 0.0:
        w2, x2, y2, z2 = -w2, -x2, -y2, -z2
        dot = -dot
    if dot > 0.9995:
        w = w1 + t * (w2 - w1)
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        z = z1 + t * (z2 - z1)
    else:
        theta_0 = math.acos(dot)
        theta = theta_0 * t
        sin_theta = math.sin(theta)
        sin_theta_0 = math.sin(theta_0)
        s1 = math.cos(theta) - dot * sin_theta / sin_theta_0
        s2 = sin_theta / sin_theta_0
        w = s1 * w1 + s2 * w2
        x = s1 * x1 + s2 * x2
        y = s1 * y1 + s2 * y2
        z = s1 * z1 + s2 * z2
    norm = math.sqrt(w * w + x * x + y * y + z * z)
    return (w / norm, x / norm, y / norm, z / norm)


def linear_interp(v1: tuple, v2: tuple, t: float) -> tuple:
    return tuple(a + t * (b - a) for a, b in zip(v1, v2))


class SensorStream:
    def __init__(self, name: str, policy: str = "KEEP_FIRST"):
        self.name = name
        self.samples: List[Tuple[float, int, Any]] = []  # List of (timestamp, source_index, data_tuple)
        self.policy = policy

        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.duration = 0.0
        self.duplicate_count = 0
        self.backward_count = 0
        self.source_was_monotonic = True
        self.rows_reordered = False
        self.largest_gap_s = 0.0

    def add_samples(self, raw_samples: List[Tuple[float, Any]]):
        if not raw_samples:
            return

        # Monotonicity check
        prev = -1e9
        for i, (ts, _) in enumerate(raw_samples):
            if ts < prev:
                self.backward_count += 1
                self.source_was_monotonic = False
            prev = ts

        sorted_samples = sorted(raw_samples, key=lambda x: x[0])
        if sorted_samples != raw_samples:
            self.rows_reordered = True

        # Deduplicate
        unique_samples = []
        prev_ts = None
        for i, (ts, data) in enumerate(sorted_samples):
            if ts == prev_ts:
                self.duplicate_count += 1
                if self.policy == "KEEP_FIRST":
                    continue
                elif self.policy == "KEEP_LAST":
                    unique_samples[-1] = (ts, i, data)
                    continue
            else:
                unique_samples.append((ts, i, data))

            if prev_ts is not None:
                gap = ts - prev_ts
                if gap > self.largest_gap_s:
                    self.largest_gap_s = gap
            prev_ts = ts

        self.samples = unique_samples
        if self.samples:
            self.start_time = self.samples[0][0]
            self.end_time = self.samples[-1][0]
            self.duration = self.end_time - self.start_time

    def get_stats(self) -> dict:
        return {
            "sample_count": len(self.samples),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "duplicate_count": self.duplicate_count,
            "backward_count": self.backward_count,
            "largest_gap_s": self.largest_gap_s,
            "source_was_monotonic": self.source_was_monotonic,
            "rows_reordered": self.rows_reordered,
            "duplicate_resolution_method": self.policy,
        }

    def interpolate(self, target_ts: float, max_gap: float, kind: str = "linear") -> Tuple[str, float, Optional[Any]]:
        if not self.samples:
            return "MISSING_STREAM", 0.0, None
        if target_ts < self.samples[0][0] or target_ts > self.samples[-1][0]:
            return "OUTSIDE_SENSOR_RANGE", 0.0, None

        import bisect

        idx = bisect.bisect_left(self.samples, (target_ts, -1, None))

        if idx == 0:
            if self.samples[0][0] == target_ts:
                return "EXACT", 0.0, self.samples[0][2]
            return "OUTSIDE_SENSOR_RANGE", 0.0, None
        if idx == len(self.samples):
            if self.samples[-1][0] == target_ts:
                return "EXACT", 0.0, self.samples[-1][2]
            return "OUTSIDE_SENSOR_RANGE", 0.0, None

        t1, i1, d1 = self.samples[idx - 1]
        t2, i2, d2 = self.samples[idx]

        if target_ts == t1:
            return "EXACT", 0.0, d1
        if target_ts == t2:
            return "EXACT", 0.0, d2

        if t2 - t1 > max_gap:
            return "GAP_TOO_LARGE", min(target_ts - t1, t2 - target_ts), None

        dt = target_ts - t1
        frac = dt / (t2 - t1)

        if kind == "linear":
            res = linear_interp(d1, d2, frac)
        elif kind == "slerp":
            res = quaternion_slerp(d1, d2, frac)
        elif kind == "gps":
            ecef1 = geodetic_to_ecef(*d1)
            ecef2 = geodetic_to_ecef(*d2)
            ecef_interp = linear_interp(ecef1, ecef2, frac)
            res = ecef_to_geodetic(*ecef_interp)
        else:
            res = None

        return "INTERPOLATED", min(target_ts - t1, t2 - target_ts), res


def run_synchronization(mission_dir: Path):
    telemetry_dir = mission_dir / "telemetry"

    frames = []
    if (telemetry_dir / "frame_timestamps.csv").exists():
        with open(telemetry_dir / "frame_timestamps.csv") as f:
            reader = csv.DictReader(f)
            for r in reader:
                frames.append(
                    {
                        "frame_index": int(r["frame_index"]),
                        "ts": float(r["canonical_unix_timestamp"]),
                        "source": r.get("source_identifier", ""),
                    }
                )

    if not frames:
        print("No frames found, skipping sync.")
        return

    frames.sort(key=lambda x: x["ts"])
    mission_start = float(frames[0]["ts"])
    mission_end = float(frames[-1]["ts"])

    gps_stream = SensorStream("gps")
    accel_stream = SensorStream("accel")
    gyro_stream = SensorStream("gyro")
    baro_stream = SensorStream("barometer")
    quat_stream = SensorStream("quaternion")

    if (telemetry_dir / "gps.csv").exists():
        raw = []
        with open(telemetry_dir / "gps.csv") as f:
            for r in csv.DictReader(f):
                raw.append((float(r["canonical_unix_timestamp"]), (float(r["lat"]), float(r["lon"]), float(r["alt"]))))
        gps_stream.add_samples(raw)

    if (telemetry_dir / "imu.csv").exists():
        raw_accel = []
        raw_gyro = []
        raw_quat = []
        with open(telemetry_dir / "imu.csv") as f:
            for r in csv.DictReader(f):
                ts = float(r["canonical_unix_timestamp"])
                if r.get("accel_x"):
                    raw_accel.append((ts, (float(r["accel_x"]), float(r["accel_y"]), float(r["accel_z"]))))
                if r.get("gyro_x"):
                    raw_gyro.append((ts, (float(r["gyro_x"]), float(r["gyro_y"]), float(r["gyro_z"]))))
                if r.get("q_w"):
                    raw_quat.append((ts, (float(r["q_w"]), float(r["q_x"]), float(r["q_y"]), float(r["q_z"]))))
        accel_stream.add_samples(raw_accel)
        gyro_stream.add_samples(raw_gyro)
        quat_stream.add_samples(raw_quat)

    if (telemetry_dir / "barometer.csv").exists():
        raw = []
        with open(telemetry_dir / "barometer.csv") as f:
            for r in csv.DictReader(f):
                raw.append((float(r["canonical_unix_timestamp"]), (float(r["pressure"]), 0.0, 0.0)))
        baro_stream.add_samples(raw)

    sync_records = []

    max_gap_gps = 2.0
    max_gap_imu = 0.05
    max_gap_baro = 0.5

    for frm in frames:
        fts = float(frm["ts"])
        g_stat, g_dt, g_val = gps_stream.interpolate(fts, max_gap_gps, "gps")
        a_stat, a_dt, a_val = accel_stream.interpolate(fts, max_gap_imu, "linear")
        gy_stat, gy_dt, gy_val = gyro_stream.interpolate(fts, max_gap_imu, "linear")
        q_stat, q_dt, q_val = quat_stream.interpolate(fts, max_gap_imu, "slerp")
        b_stat, b_dt, b_val = baro_stream.interpolate(fts, max_gap_baro, "linear")

        rec = {
            "frame_index": frm["frame_index"],
            "frame_timestamp": fts,
            "gps_status": g_stat,
            "gps_dt_s": g_dt,
            "accel_status": a_stat,
            "accel_dt_s": a_dt,
            "gyro_status": gy_stat,
            "gyro_dt_s": gy_dt,
            "quat_status": q_stat,
            "quat_dt_s": q_dt,
            "barometer_status": b_stat,
            "barometer_dt_s": b_dt,
        }
        if g_val:
            rec["lat"], rec["lon"], rec["alt"] = g_val
        if a_val:
            rec["accel_x"], rec["accel_y"], rec["accel_z"] = a_val
        if gy_val:
            rec["gyro_x"], rec["gyro_y"], rec["gyro_z"] = gy_val
        if q_val:
            rec["q_w"], rec["q_x"], rec["q_y"], rec["q_z"] = q_val
        if b_val:
            rec["pressure"] = b_val[0]

        sync_records.append(rec)

    fields = [
        "frame_index",
        "frame_timestamp",
        "gps_status",
        "gps_dt_s",
        "lat",
        "lon",
        "alt",
        "accel_status",
        "accel_dt_s",
        "accel_x",
        "accel_y",
        "accel_z",
        "gyro_status",
        "gyro_dt_s",
        "gyro_x",
        "gyro_y",
        "gyro_z",
        "quat_status",
        "quat_dt_s",
        "q_w",
        "q_x",
        "q_y",
        "q_z",
        "barometer_status",
        "barometer_dt_s",
        "pressure",
    ]

    with open(telemetry_dir / "synchronized_telemetry.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for rec in sync_records:
            writer.writerow({k: rec.get(k, "") for k in fields})

    def calc_overlap(stream: Any):  # type: ignore
        if stream.start_time is None:
            return None
        os = max(mission_start, stream.start_time)
        oe = min(mission_end, stream.end_time)
        dur = oe - os
        return {
            "overlap_start": os,
            "overlap_end": oe,
            "overlap_duration": dur,
            "coverage_fraction": max(0.0, dur / (mission_end - mission_start)) if mission_end > mission_start else 0.0,
        }

    meta = {}
    if (telemetry_dir / "flight_metadata.json").exists():
        with open(telemetry_dir / "flight_metadata.json") as f:
            meta = json.load(f)

    report = {
        "mission": mission_dir.parent.name,
        "absolute_time_available": meta.get("ABSOLUTE_TIME") != "NOT_AVAILABLE",
        "timebase": meta.get("timebase", "UNKNOWN"),
        "vertical_datum": meta.get("vertical_datum", "UNKNOWN"),
        "crs": meta.get("crs", "UNKNOWN"),
        "stream_statistics": {
            "gps": gps_stream.get_stats(),
            "accel": accel_stream.get_stats(),
            "gyro": gyro_stream.get_stats(),
            "quaternion": quat_stream.get_stats(),
            "barometer": baro_stream.get_stats(),
        },
        "overlap_intervals": {
            "frames_vs_gps": calc_overlap(gps_stream),
            "frames_vs_accel": calc_overlap(accel_stream),
            "frames_vs_gyro": calc_overlap(gyro_stream),
            "frames_vs_quaternion": calc_overlap(quat_stream),
            "frames_vs_barometer": calc_overlap(baro_stream),
        },
    }

    with open(telemetry_dir / "sensor_sync_report.json", "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    import sys

    run_synchronization(Path(sys.argv[1]))
