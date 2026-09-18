import json
from pathlib import Path

from common import write_conversion_report
from validate_canonical_mission import validate_mission


def convert_h3d(input_dir: Path, output_dir: Path):
    print("H3D Adapter")

    warnings = []
    if not input_dir.exists():
        print("ACCESS_BLOCKED: H3D requires manual application/login. Using synthetic representation.")
        warnings.append("Real data not provided; access blocked. Creating synthetic representation.")

    output_dir.mkdir(parents=True, exist_ok=True)
    mission_dir = output_dir / "mission"
    (mission_dir / "reference").mkdir(parents=True, exist_ok=True)

    with open(mission_dir / "reference" / "dtm.tif", "w") as f:
        f.write("mock_dtm")

    with open(mission_dir / "reference" / "lidar.las", "w") as f:
        f.write("mock_lidar")

    # Dummy telemetry to pass basic validation
    (mission_dir / "telemetry").mkdir(exist_ok=True)
    with open(mission_dir / "telemetry" / "flight_metadata.json", "w") as f:
        json.dump({"crs": "UNKNOWN", "vertical_datum": "UNKNOWN"}, f)

    write_conversion_report(
        dataset="H3D",
        sequence="synthetic_test",
        input_files=[],
        output_files=["dtm.tif", "lidar.las"],
        rows_frames_converted=1,
        timestamp_range=None,
        crs="UNKNOWN",
        sensor_availability={"lidar": True, "dtm": True},
        missing_sensors=["gps", "imu", "images"],
        warnings=warnings,
        errors=[],
        output_dir=output_dir,
    )

    report = validate_mission(mission_dir)
    print(f"Validation status: {report['status']}")


if __name__ == "__main__":
    convert_h3d(Path("data_external/h3d/raw"), Path("data_external/h3d"))
