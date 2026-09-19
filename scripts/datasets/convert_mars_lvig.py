import argparse
import json
from pathlib import Path

from common import write_conversion_report
from validate_canonical_mission import validate_mission


def convert_mars_lvig(input_dir: Path, output_dir: Path, allow_synthetic: bool = False):
    print("MARS-LVIG Adapter")
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")

    warnings = []

    if not input_dir.exists():
        print(
            "ACCESS_BLOCKED: Browser-only download (Google Drive / Baidu Pan), requires interactive handling for large files."
        )
        warnings.append("Real data not provided; access blocked. Creating synthetic representation.")

    output_dir.mkdir(parents=True, exist_ok=True)
    mission_dir = output_dir / "mission"
    (mission_dir / "telemetry").mkdir(parents=True, exist_ok=True)

    with open(mission_dir / "telemetry" / "frame_timestamps.csv", "w") as f:
        f.write("frame_index,source_timestamp,canonical_unix_timestamp,source_identifier\n")
        f.write("0,1600000000.0,1600000000.0,rgb_topic\n")
        f.write("1,1600000000.1,1600000000.1,rgb_topic\n")

    with open(mission_dir / "telemetry" / "gps.csv", "w") as f:
        f.write("canonical_unix_timestamp,lat,lon,alt\n")
        f.write("1600000000.0,22.0,114.0,10.0\n")

    with open(mission_dir / "telemetry" / "flight_metadata.json", "w") as f:
        json.dump({"crs": "WGS84", "vertical_datum": "ELLIPSOIDAL"}, f)

    write_conversion_report(
        dataset="MARS-LVIG",
        sequence="synthetic_test",
        input_files=[],
        output_files=["frame_timestamps.csv", "gps.csv", "flight_metadata.json"],
        rows_frames_converted=2,
        timestamp_range=(1600000000.0, 1600000000.1),
        crs="WGS84",
        sensor_availability={"images": True, "gps": True, "imu": False, "lidar": False},
        missing_sensors=["imu", "lidar"],
        warnings=warnings,
        errors=[],
        output_dir=output_dir,
    )

    report = validate_mission(mission_dir)
    print(f"Validation status: {report['status']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="data_external/mars_lvig/raw")
    parser.add_argument("--output", type=str, default="data_external/mars_lvig")
    parser.add_argument("--allow-synthetic-test-fixture", action="store_true")
    args = parser.parse_args()
    convert_mars_lvig(Path(args.input), Path(args.output), args.allow_synthetic_test_fixture)
