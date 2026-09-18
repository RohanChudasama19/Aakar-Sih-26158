import json
from pathlib import Path


def write_conversion_report(
    dataset: str,
    sequence: str,
    input_files: list[str],
    output_files: list[str],
    rows_frames_converted: int,
    timestamp_range: tuple[float, float] | None,
    crs: str,
    sensor_availability: dict[str, bool],
    missing_sensors: list[str],
    warnings: list[str],
    errors: list[str],
    output_dir: Path,
):
    report = {
        "dataset": dataset,
        "sequence": sequence,
        "input_files": input_files,
        "output_files": output_files,
        "rows_frames_converted": rows_frames_converted,
        "timestamp_range": timestamp_range,
        "crs": crs,
        "sensor_availability": sensor_availability,
        "missing_sensors": missing_sensors,
        "warnings": warnings,
        "errors": errors,
    }
    with open(output_dir / "conversion_report.json", "w") as f:
        json.dump(report, f, indent=4)
