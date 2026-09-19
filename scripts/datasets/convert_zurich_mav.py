import argparse
import json
import sys
import zipfile
from pathlib import Path

from common import write_conversion_report
from dataset_manifest import create_manifest
from validate_canonical_mission import validate_mission


def convert_zurich_mav(input_dir: Path, output_dir: Path, allow_synthetic: bool = False):
    print("Zurich Urban MAV Adapter")

    zip_path = input_dir / "AGZ_subset.zip"

    output_dir.mkdir(parents=True, exist_ok=True)
    mission_dir = output_dir / "mission"
    (mission_dir / "telemetry").mkdir(parents=True, exist_ok=True)
    (mission_dir / "control").mkdir(parents=True, exist_ok=True)

    warnings = []

    if not zip_path.exists():
        if not allow_synthetic:
            print("ERROR: STRICT_REAL_DATA is enforced.")
            print("ACCESS_BLOCKED: AGZ_subset.zip not found in data_external/zurich_mav/raw/")
            sys.exit(1)

        print("WARNING: Real data missing. Falling back to synthetic test fixture.")
        warnings.append("Real data not provided; access blocked. Creating synthetic representation.")

        with open(mission_dir / "telemetry" / "frame_timestamps.csv", "w") as f:
            f.write("frame_index,source_timestamp,canonical_time_s,source_identifier\n")
            f.write("0,1000000.0,1600000000.0,frame0000.png\n")

        with open(mission_dir / "telemetry" / "imu.csv", "w") as f:
            f.write("canonical_time_s,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z\n")
            f.write("1600000000.0,0.0,0.0,9.81,0.0,0.0,0.0\n")

        with open(mission_dir / "telemetry" / "flight_metadata.json", "w") as f:
            json.dump({"crs": "UNKNOWN", "vertical_datum": "UNKNOWN"}, f)

        write_conversion_report(
            dataset="Zurich MAV",
            sequence="synthetic_test",
            input_files=[],
            output_files=["frame_timestamps.csv", "imu.csv", "flight_metadata.json"],
            rows_frames_converted=1,
            timestamp_range=(1600000000.0, 1600000000.0),
            crs="UNKNOWN",
            sensor_availability={"images": True, "imu": True},
            missing_sensors=["gps", "barometer"],
            warnings=warnings,
            errors=[],
            output_dir=output_dir,
        )
        report = validate_mission(mission_dir)
        return

    def microsec_to_canonical(ts_str):
        try:
            return float(ts_str) / 1000000.0
        except ValueError:
            return 0.0

    def process_and_sort_csv(rows):
        orig_count = len(rows)
        backward_count = 0
        duplicate_count = 0
        largest_neg_jump = 0.0

        prev_ts = -1.0
        for r in rows:
            ts = r[0]
            if ts < prev_ts:
                backward_count += 1
                largest_neg_jump = min(largest_neg_jump, ts - prev_ts)
            elif ts == prev_ts:
                duplicate_count += 1
            prev_ts = ts

        sorted_rows = sorted(rows, key=lambda x: x[0])
        rows_reordered = rows != sorted_rows

        return sorted_rows, orig_count, backward_count, duplicate_count, largest_neg_jump, rows_reordered

    with zipfile.ZipFile(zip_path, "r") as z:
        # GPS
        gps_rows = []
        img_timestamps = {}
        with z.open("AGZ_subset/Log Files/OnboardGPS.csv") as f:
            lines = [line_item.decode("utf-8").strip() for line_item in f.readlines()]
            for line in lines[1:]:
                if not line:
                    continue
                parts = line.split(",")
                ts = microsec_to_canonical(parts[0])
                imgid = parts[1].strip()
                lat = float(parts[2])
                lon = float(parts[3])
                alt = float(parts[4])
                gps_rows.append((ts, lat, lon, alt))
                if imgid and int(imgid) > 0:
                    img_timestamps[int(imgid)] = ts

        gps_sorted, gps_orig, gps_back, gps_dup, gps_neg, gps_reorder = process_and_sort_csv(gps_rows)

        with open(mission_dir / "telemetry" / "gps.csv", "w") as f:
            f.write("canonical_time_s,lat,lon,alt\n")
            for r in gps_sorted:
                f.write(f"{r[0]},{r[1]},{r[2]},{r[3]}\n")

        # Frames
        img_files = [n for n in z.namelist() if n.startswith("AGZ_subset/MAV Images/") and n.lower().endswith(".jpg")]
        img_files.sort()
        with open(mission_dir / "telemetry" / "frame_timestamps.csv", "w") as f:
            f.write("frame_index,source_timestamp,canonical_time_s,source_identifier\n")
            for idx, n in enumerate(img_files):
                fname = Path(n).name
                imgid = int(fname.split(".")[0])
                ts = img_timestamps.get(imgid, 0.0)
                f.write(f"{idx},{ts},{ts},{fname}\n")

        # IMU Accel & Gyro
        # imu_rows removed
        imu_dict = {}

        with z.open("AGZ_subset/Log Files/RawAccel.csv") as f:
            lines = [line_item.decode("utf-8").strip() for line_item in f.readlines()]
            for line in lines[1:]:
                if not line:
                    continue
                parts = line.split(",")
                ts = microsec_to_canonical(parts[0])
                if ts not in imu_dict:
                    imu_dict[ts] = {}
                imu_dict[ts]["accel"] = (float(parts[2]), float(parts[3]), float(parts[4]))

        with z.open("AGZ_subset/Log Files/RawGyro.csv") as f:
            lines = [line_item.decode("utf-8").strip() for line_item in f.readlines()]
            for line in lines[1:]:
                if not line:
                    continue
                parts = line.split(",")
                ts = microsec_to_canonical(parts[0])
                if ts not in imu_dict:
                    imu_dict[ts] = {}
                imu_dict[ts]["gyro"] = (float(parts[2]), float(parts[3]), float(parts[4]))

        # Convert to list of tuples for sorting
        imu_list = []
        for ts, vals in imu_dict.items():
            imu_list.append((ts, vals.get("accel"), vals.get("gyro")))

        imu_sorted, imu_orig, imu_back, imu_dup, imu_neg, imu_reorder = process_and_sort_csv(imu_list)

        with open(mission_dir / "telemetry" / "imu.csv", "w") as f:
            f.write("canonical_time_s,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z\n")
            for r in imu_sorted:
                ts = r[0]
                ax, ay, az = r[1] if r[1] else ("", "", "")
                gx, gy, gz = r[2] if r[2] else ("", "", "")
                f.write(f"{ts},{ax},{ay},{az},{gx},{gy},{gz}\n")

        # Barometer
        baro_rows = []
        with z.open("AGZ_subset/Log Files/BarometricPressure.csv") as f:
            lines = [line_item.decode("utf-8").strip() for line_item in f.readlines()]
            for line in lines[1:]:
                if not line:
                    continue
                parts = line.split(",")
                ts = microsec_to_canonical(parts[0])
                pressure = float(parts[1])
                temp = float(parts[3])
                baro_rows.append((ts, pressure, temp))

        baro_sorted, baro_orig, baro_back, baro_dup, baro_neg, baro_reorder = process_and_sort_csv(baro_rows)
        with open(mission_dir / "telemetry" / "barometer.csv", "w") as f:
            f.write("canonical_time_s,pressure,temperature\n")
            for r in baro_sorted:
                f.write(f"{r[0]},{r[1]},{r[2]}\n")

    with open(mission_dir / "telemetry" / "flight_metadata.json", "w") as f:
        json.dump(
            {
                "crs": "WGS84",
                "vertical_datum": "ELLIPSOIDAL",
                "height_type": "UNKNOWN",
                "units": "meters",
                "timebase": "relative_microseconds",
                "ABSOLUTE_TIME": "NOT_AVAILABLE",
                "imu_orientation_convention": "UNKNOWN",
            },
            f,
            indent=2,
        )

    create_manifest(
        dataset_name="Zurich Urban MAV",
        source_url="https://download.ifi.uzh.ch/rpg/AGZ_data/AGZ_subset.zip",
        source_sequence="AGZ_subset",
        local_files=[zip_path],
        license_reference="Academic research use",
        original_format="ZIP",
        output_dir=output_dir,
    )

    write_conversion_report(
        dataset="Zurich MAV",
        sequence="AGZ_subset",
        input_files=["AGZ_subset.zip"],
        output_files=["frame_timestamps.csv", "gps.csv", "imu.csv", "barometer.csv", "flight_metadata.json"],
        rows_frames_converted=len(img_files),
        timestamp_range=(min(r[0] for r in gps_rows), max(r[0] for r in gps_rows)),
        crs="WGS84",
        sensor_availability={"images": True, "gps": True, "imu": True, "barometer": True},
        missing_sensors=["rtk"],
        warnings=warnings,
        errors=[],
        output_dir=output_dir,
        additional_info={
            "gps_sorting": {
                "original_row_count": gps_orig,
                "duplicate_timestamp_count": gps_dup,
                "backward_timestamp_count": gps_back,
                "largest_negative_jump_s": gps_neg,
                "rows_reordered": gps_reorder,
                "sorted_output": True,
            },
            "imu_sorting": {
                "original_row_count": imu_orig,
                "duplicate_timestamp_count": imu_dup,
                "backward_timestamp_count": imu_back,
                "largest_negative_jump_s": imu_neg,
                "rows_reordered": imu_reorder,
                "sorted_output": True,
            },
            "baro_sorting": {
                "original_row_count": baro_orig,
                "duplicate_timestamp_count": baro_dup,
                "backward_timestamp_count": baro_back,
                "largest_negative_jump_s": baro_neg,
                "rows_reordered": baro_reorder,
                "sorted_output": True,
            },
            "IMU_FRAME_STATUS": "UNKNOWN",
        },
    )

    report = validate_mission(mission_dir)
    print(f"Validation status: {report['status']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="data_external/zurich_mav/raw")
    parser.add_argument("--output", type=str, default="data_external/zurich_mav")
    parser.add_argument("--allow-synthetic-test-fixture", action="store_true")
    args = parser.parse_args()
    convert_zurich_mav(Path(args.input), Path(args.output), args.allow_synthetic_test_fixture)
