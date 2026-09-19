import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "scripts" / "datasets"))
from validate_canonical_mission import validate_mission


def test_validate_mission_valid(tmp_path):
    mission_dir = tmp_path / "mission"

    (mission_dir / "video").mkdir(parents=True)
    (mission_dir / "telemetry").mkdir(parents=True)

    with open(mission_dir / "telemetry" / "frame_timestamps.csv", "w") as f:
        f.write("frame_index,source_timestamp,canonical_time_s,source_identifier\n")
        f.write("0,1.0,1.0,img1\n")
        f.write("1,1.1,1.1,img2\n")  # monotonic

    with open(mission_dir / "telemetry" / "flight_metadata.json", "w") as f:
        json.dump({"crs": "WGS84", "vertical_datum": "ELLIPSOIDAL"}, f)

    report = validate_mission(mission_dir)
    assert report["status"] == "VALID"
    assert len(report["errors"]) == 0


def test_validate_mission_non_monotonic_timestamp(tmp_path):
    mission_dir = tmp_path / "mission"
    (mission_dir / "telemetry").mkdir(parents=True)

    with open(mission_dir / "telemetry" / "frame_timestamps.csv", "w") as f:
        f.write("frame_index,source_timestamp,canonical_time_s,source_identifier\n")
        f.write("0,1.5,1.5,img1\n")
        f.write("1,1.2,1.2,img2\n")  # not monotonic

    report = validate_mission(mission_dir)
    assert report["status"] == "VALID_WITH_WARNINGS" or report["status"] == "INVALID"
    # Actually validate_mission puts schema errors in "errors", making it INVALID
    assert report["status"] == "INVALID"
    assert any("not monotonic" in e for e in report["errors"])


def test_validate_mission_missing_schema_columns(tmp_path):
    mission_dir = tmp_path / "mission"
    (mission_dir / "telemetry").mkdir(parents=True)

    with open(mission_dir / "telemetry" / "frame_timestamps.csv", "w") as f:
        f.write("frame_index,source_timestamp\n")
        f.write("0,1.5\n")

    report = validate_mission(mission_dir)
    assert report["status"] == "INVALID"
    assert any("missing required columns" in e for e in report["errors"])
