import shutil
import urllib.request
import zipfile
from pathlib import Path

from common import write_conversion_report
from dataset_manifest import create_manifest
from validate_canonical_mission import validate_mission


def prepare_ppph_uav():
    base_dir = Path("data_external/ppph_uav")
    base_dir.mkdir(parents=True, exist_ok=True)

    zip_path = base_dir / "6.Example.zip"
    url = "https://zenodo.org/api/records/18981905/files/6.Example.zip/content"

    if not zip_path.exists():
        print("Downloading PPPH-UAV Example Data...")
        urllib.request.urlretrieve(url, zip_path)

    extract_dir = base_dir / "extracted"
    if not extract_dir.exists():
        print("Extracting...")
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_dir)

    mission_dir = base_dir / "mission"
    mission_dir.mkdir(exist_ok=True)

    # Required canonical dirs
    (mission_dir / "gnss" / "rinex").mkdir(parents=True, exist_ok=True)
    (mission_dir / "telemetry").mkdir(exist_ok=True)

    # In PPPH-UAV example, RINEX and precise files are in 6.Example folder
    example_folder = extract_dir / "6.Example"
    copied_files = []

    if example_folder.exists():
        for f in example_folder.glob("*.*"):
            dest = mission_dir / "gnss" / "rinex" / f.name
            shutil.copy2(f, dest)
            copied_files.append(dest)

    # Mocking a frame_timestamps.csv if they provided image tags, but we'll leave it as we just ingest RINEX

    # Create manifest
    create_manifest(
        dataset_name="PPPH-UAV Example Data",
        source_url=url,
        source_sequence="6.Example",
        local_files=[zip_path],
        license_reference="CC-BY-4.0",
        original_format="ZIP",
        output_dir=base_dir,
    )

    # Conversion report
    write_conversion_report(
        dataset="PPPH-UAV Example",
        sequence="6.Example",
        input_files=[str(zip_path.name)],
        output_files=[str(p.name) for p in copied_files],
        rows_frames_converted=0,
        timestamp_range=None,
        crs="UNKNOWN",
        sensor_availability={"gnss": True},
        missing_sensors=["images", "gps", "imu", "barometer"],
        warnings=["No full matching drone video imagery, only GNSS files ingested"],
        errors=[],
        output_dir=base_dir,
    )

    # Canonical validation
    report = validate_mission(mission_dir)
    print(f"Validation status: {report['status']}")


if __name__ == "__main__":
    prepare_ppph_uav()
