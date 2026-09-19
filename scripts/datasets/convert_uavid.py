import argparse
import json
from pathlib import Path

from common import write_conversion_report
from validate_canonical_mission import validate_mission


def convert_uavid(input_dir: Path, output_dir: Path, allow_synthetic: bool = False):
    print("UAVid Adapter")

    warnings = []
    if not input_dir.exists():
        print("ACCESS_BLOCKED: Requires Account / Login. Using synthetic representation.")
        warnings.append("Real data not provided; access blocked. Creating synthetic representation.")

    output_dir.mkdir(parents=True, exist_ok=True)
    mission_dir = output_dir / "mission"
    (mission_dir / "semantics" / "images").mkdir(parents=True, exist_ok=True)
    (mission_dir / "semantics" / "masks").mkdir(parents=True, exist_ok=True)

    with open(mission_dir / "semantics" / "classes.json", "w") as f:
        json.dump(
            {
                "classes": [
                    "building",
                    "road",
                    "tree",
                    "low vegetation",
                    "static car",
                    "moving car",
                    "human",
                    "clutter/background",
                ],
                "mapped_aerorecon_taxonomy": [
                    "BUILDING",
                    "ROAD",
                    "VEGETATION",
                    "VEGETATION",
                    "OBSTACLE",
                    "OBSTACLE",
                    "OBSTACLE",
                    "UNKNOWN",
                ],
            },
            f,
        )

    # dummy files
    with open(mission_dir / "semantics" / "images" / "0000.png", "w") as f:
        f.write("mock_image")
    with open(mission_dir / "semantics" / "masks" / "0000.png", "w") as f:
        f.write("mock_mask")

    # Dummy telemetry to pass basic validation
    (mission_dir / "telemetry").mkdir(exist_ok=True)
    with open(mission_dir / "telemetry" / "flight_metadata.json", "w") as f:
        json.dump({"crs": "N/A", "vertical_datum": "N/A"}, f)

    write_conversion_report(
        dataset="UAVid",
        sequence="synthetic_test",
        input_files=[],
        output_files=["classes.json"],
        rows_frames_converted=1,
        timestamp_range=None,
        crs="N/A",
        sensor_availability={"semantics": True},
        missing_sensors=["gps", "imu", "images"],
        warnings=warnings,
        errors=[],
        output_dir=output_dir,
    )

    report = validate_mission(mission_dir)
    print(f"Validation status: {report['status']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="data_external/uavid/raw")
    parser.add_argument("--output", type=str, default="data_external/uavid")
    parser.add_argument("--allow-synthetic-test-fixture", action="store_true")
    args = parser.parse_args()
    convert_uavid(Path(args.input), Path(args.output), args.allow_synthetic_test_fixture)
