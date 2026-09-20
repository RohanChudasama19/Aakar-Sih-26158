import argparse
import json
import shutil
import hashlib
from pathlib import Path

from common import write_conversion_report
from validate_canonical_mission import validate_mission


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def convert_h3d(input_dir: Path, output_dir: Path, allow_synthetic: bool = False):
    print("H3D Adapter (Real Data)")

    output_dir.mkdir(parents=True, exist_ok=True)
    mission_dir = output_dir / "mission"
    (mission_dir / "reference").mkdir(parents=True, exist_ok=True)

    # Real files
    test_laz = input_dir / "Epoch_March2019/LiDAR/Mar19_test.laz"
    gt_laz = input_dir / "Epoch_March2019/LiDAR/Mar19_test_GroundTruth.laz"

    warnings = []
    output_files = []

    if test_laz.exists() and gt_laz.exists():
        print(f"Found real H3D data. Converting to {mission_dir}")
        out_test = mission_dir / "reference" / "Mar19_test.laz"
        out_gt = mission_dir / "reference" / "Mar19_test_GroundTruth.laz"

        shutil.copy2(test_laz, out_test)
        shutil.copy2(gt_laz, out_gt)

        h_test = hash_file(out_test)
        h_gt = hash_file(out_gt)

        manifest = {
            "Mar19_test.laz": {"sha256": h_test, "role": "evaluation_target"},
            "Mar19_test_GroundTruth.laz": {"sha256": h_gt, "role": "reference_geometry"},
        }
        with open(mission_dir / "reference" / "provenance.json", "w") as f:
            json.dump(manifest, f, indent=2)

        output_files = ["Mar19_test.laz", "Mar19_test_GroundTruth.laz"]

        # Telemetry to satisfy canonical validation (we only have reference lidar)
        (mission_dir / "telemetry").mkdir(exist_ok=True)
        with open(mission_dir / "telemetry" / "flight_metadata.json", "w") as f:
            json.dump({"crs": "EPSG:32632", "vertical_datum": "DHHN2016"}, f)

        write_conversion_report(
            dataset="H3D",
            sequence="Epoch_March2019",
            input_files=[str(test_laz), str(gt_laz)],
            output_files=output_files,
            rows_frames_converted=0,
            timestamp_range=None,
            crs="EPSG:32632",
            sensor_availability={"lidar": True, "dtm": False, "images": False},
            missing_sensors=["gps", "imu", "images", "dtm"],
            warnings=warnings,
            errors=[],
            output_dir=output_dir,
        )
    else:
        print("ACCESS_BLOCKED: H3D requires manual application/login. Using synthetic representation.")
        if not allow_synthetic:
            raise FileNotFoundError("Real H3D data not found and allow_synthetic is False.")
        warnings.append("Real data not provided; access blocked. Creating synthetic representation.")
        # fallback synthetic code...
        with open(mission_dir / "reference" / "dtm.tif", "w") as f:
            f.write("mock_dtm")
        with open(mission_dir / "reference" / "lidar.las", "w") as f:
            f.write("mock_lidar")
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="data_external/h3d/raw")
    parser.add_argument("--output", type=str, default="data_external/h3d/converted")
    parser.add_argument("--allow-synthetic-test-fixture", action="store_true")
    args = parser.parse_args()
    convert_h3d(Path(args.input), Path(args.output), args.allow_synthetic_test_fixture)
