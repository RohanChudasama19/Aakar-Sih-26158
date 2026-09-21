import json
from pathlib import Path

from common import write_conversion_report


def convert_uavid(input_dir: Path, output_dir: Path, allow_synthetic: bool = False):
    print("UAVid Adapter")

    if not input_dir.exists() or not any(input_dir.iterdir()):
        print("ACCESS_BLOCKED: UAVid requires manual download.")
        if not allow_synthetic:
            write_conversion_report(
                dataset="UAVid",
                sequence="none",
                input_files=[],
                output_files=[],
                rows_frames_converted=0,
                timestamp_range=None,
                crs="UNKNOWN",
                sensor_availability={},
                missing_sensors=["images", "labels"],
                warnings=["MANUAL_DOWNLOAD_REQUIRED: UAVid data not found. Synthetic mode disabled."],
                errors=[],
                output_dir=output_dir,
            )
            return

        print("Generating synthetic UAVid representation for pipeline testing...")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "train").mkdir(exist_ok=True)
        (output_dir / "val").mkdir(exist_ok=True)
        (output_dir / "test").mkdir(exist_ok=True)

        sem_dir = output_dir / "mission" / "semantics"
        sem_dir.mkdir(parents=True, exist_ok=True)
        with open(sem_dir / "classes.json", "w") as f:
            json.dump(
                {
                    "0": "UNKNOWN",
                    "1": "BUILDING",
                    "2": "ROAD",
                    "3": "OBSTACLE",
                    "4": "VEGETATION",
                    "5": "VEGETATION",
                    "6": "DYNAMIC_OBJECT",
                    "7": "DYNAMIC_OBJECT",
                },
                f,
            )

        with open(output_dir / "train" / "dummy.png", "w") as f:
            f.write("mock")

        write_conversion_report(
            dataset="UAVid",
            sequence="synthetic",
            input_files=[],
            output_files=["train/dummy.png"],
            rows_frames_converted=1,
            timestamp_range=None,
            crs="UNKNOWN",
            sensor_availability={"images": True, "labels": True},
            missing_sensors=[],
            warnings=["MANUAL_DOWNLOAD_REQUIRED: UAVid data not found. Using synthetic test fixture."],
            errors=[],
            output_dir=output_dir,
        )
        return
