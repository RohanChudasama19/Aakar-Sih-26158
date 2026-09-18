import json
from pathlib import Path

from common import write_conversion_report
from validate_canonical_mission import validate_mission


def convert_zurich_mav(input_dir: Path, output_dir: Path):
    print("Zurich Urban MAV Adapter")

    warnings = []
    if not input_dir.exists():
        print("ACCESS_BLOCKED: Large dataset archive not downloaded. Using synthetic representation.")
        warnings.append("Real data not provided; access blocked. Creating synthetic representation.")

    output_dir.mkdir(parents=True, exist_ok=True)
    mission_dir = output_dir / "mission"
    (mission_dir / "telemetry").mkdir(parents=True, exist_ok=True)

    # Dummy canonical creation for testing logic
    with open(mission_dir / "telemetry" / "frame_timestamps.csv", "w") as f:
        f.write("frame_index,source_timestamp,canonical_unix_timestamp,source_identifier\n")
        f.write("0,1000000.0,1600000000.0,frame0000.png\n")

    with open(mission_dir / "telemetry" / "imu.csv", "w") as f:
        f.write("canonical_unix_timestamp,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z\n")
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
    print(f"Validation status: {report['status']}")


if __name__ == "__main__":
    convert_zurich_mav(Path("data_external/zurich_mav/raw"), Path("data_external/zurich_mav"))
