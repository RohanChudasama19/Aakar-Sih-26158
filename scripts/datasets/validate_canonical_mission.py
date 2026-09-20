import csv
import json
import sys
from pathlib import Path


def validate_csv_schema(file_path: Path, required_columns: set) -> list[str]:
    errors = []
    if not file_path.exists():
        return errors
    try:
        with open(file_path, newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return [f"{file_path.name} is empty or missing headers."]
            missing = required_columns - set(reader.fieldnames)
            if missing:
                errors.append(f"{file_path.name} is missing required columns: {missing}")

            # Check monotonicity of canonical_time_s if present
            if "canonical_time_s" in reader.fieldnames:
                prev_ts = -1.0
                for row_idx, row in enumerate(reader):
                    try:
                        ts = float(row.get("canonical_time_s") or row.get("canonical_unix_timestamp") or "0.0")
                        if ts < prev_ts:
                            errors.append(
                                f"{file_path.name} row {row_idx + 2}: timestamp {ts} is strictly earlier than previous {prev_ts} (not monotonic)."
                            )
                        prev_ts = ts
                    except ValueError:
                        errors.append(
                            f"{file_path.name} row {row_idx + 2}: invalid canonical_time_s '{row['canonical_time_s']}'"
                        )
    except Exception as e:
        errors.append(f"Failed to read {file_path.name}: {e}")
    return errors


def validate_mission(mission_dir: Path) -> dict:
    mission_dir = Path(mission_dir)
    report = {"status": "VALID", "errors": [], "warnings": []}

    # Required dirs
    for d in ["video", "telemetry"]:
        if not (mission_dir / d).exists():
            report["warnings"].append(f"Missing recommended directory: {d}")

    # Schemas
    schemas = {
        "telemetry/frame_timestamps.csv": {
            "frame_index",
            "source_timestamp",
            "canonical_time_s",
            "source_identifier",
        },
        "telemetry/gps.csv": {"canonical_time_s", "lat", "lon", "alt"},
        "telemetry/imu.csv": {"canonical_time_s"},
        "telemetry/barometer.csv": {"canonical_time_s", "pressure"},
        "gnss/rtk_ppk.csv": {"canonical_time_s", "lat", "lon", "height", "quality"},
        "control/gcps.csv": {"checkpoint_id", "latitude", "longitude", "elevation", "role"},
    }

    for rel_path, req_cols in schemas.items():
        p = mission_dir / rel_path
        if p.exists():
            report["errors"].extend(validate_csv_schema(p, req_cols))

    # Metadata
    metadata_file = mission_dir / "telemetry/flight_metadata.json"
    if metadata_file.exists():
        try:
            with open(metadata_file) as f:
                meta = json.load(f)
                for k in ["crs", "vertical_datum"]:
                    if k not in meta:
                        report["errors"].append(f"flight_metadata.json missing required key: {k}")
        except json.JSONDecodeError:
            report["errors"].append("flight_metadata.json is invalid JSON")

    if report["errors"]:
        report["status"] = "INVALID"
    elif report["warnings"]:
        report["status"] = "VALID_WITH_WARNINGS"

    report_path = mission_dir / "canonical_validation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=4)

    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_canonical_mission.py <mission_dir>")
        sys.exit(1)
    rep = validate_mission(Path(sys.argv[1]))
    print(json.dumps(rep, indent=2))
    sys.exit(0 if rep["status"] != "INVALID" else 1)
