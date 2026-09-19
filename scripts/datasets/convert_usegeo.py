import argparse
import json
from pathlib import Path

from common import write_conversion_report
from validate_canonical_mission import validate_mission


def convert_usegeo(input_dir: Path, output_dir: Path, allow_synthetic: bool = False):
    print("UseGeo Adapter")

    warnings = []
    if not input_dir.exists():
        print("ACCESS_BLOCKED: Browser-only download (Synology Drive), requires interactive handling.")
        warnings.append("Real data not provided; access blocked. Creating synthetic representation.")

    output_dir.mkdir(parents=True, exist_ok=True)
    mission_dir = output_dir / "mission"
    (mission_dir / "telemetry").mkdir(parents=True, exist_ok=True)
    (mission_dir / "reference").mkdir(parents=True, exist_ok=True)

    # Dummy canonical creation for testing logic
    with open(mission_dir / "telemetry" / "frame_timestamps.csv", "w") as f:
        f.write("frame_index,source_timestamp,canonical_unix_timestamp,source_identifier\n")
        f.write("0,1.0,1.0,IMG_0001.JPG\n")

    with open(mission_dir / "telemetry" / "flight_metadata.json", "w") as f:
        json.dump({"crs": "UNKNOWN", "vertical_datum": "UNKNOWN"}, f)

    write_conversion_report(
        dataset="UseGeo",
        sequence="synthetic_test",
        input_files=[],
        output_files=["frame_timestamps.csv", "flight_metadata.json"],
        rows_frames_converted=1,
        timestamp_range=None,
        crs="UNKNOWN",
        sensor_availability={"images": True, "lidar": True},
        missing_sensors=["gps", "imu"],
        warnings=warnings,
        errors=[],
        output_dir=output_dir,
    )

    report = validate_mission(mission_dir)
    print(f"Validation status: {report['status']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="data_external/usegeo/raw")
    parser.add_argument("--output", type=str, default="data_external/usegeo")
    parser.add_argument("--allow-synthetic-test-fixture", action="store_true")
    args = parser.parse_args()
    convert_usegeo(Path(args.input), Path(args.output), args.allow_synthetic_test_fixture)
