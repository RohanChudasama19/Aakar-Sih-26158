import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "scripts" / "datasets"))
from convert_h3d import convert_h3d
from convert_mars_lvig import convert_mars_lvig
from convert_uavid import convert_uavid
from convert_usegeo import convert_usegeo
from convert_zurich_mav import convert_zurich_mav


def test_mars_lvig_adapter_synthetic(tmp_path):
    input_dir = tmp_path / "raw"
    output_dir = tmp_path / "out"
    convert_mars_lvig(input_dir, output_dir)
    assert (output_dir / "mission" / "telemetry" / "frame_timestamps.csv").exists()


def test_usegeo_adapter_synthetic(tmp_path):
    input_dir = tmp_path / "raw"
    output_dir = tmp_path / "out"
    convert_usegeo(input_dir, output_dir)
    assert (output_dir / "mission" / "telemetry" / "frame_timestamps.csv").exists()


def test_zurich_mav_adapter_synthetic(tmp_path):
    input_dir = tmp_path / "raw"
    output_dir = tmp_path / "out"
    convert_zurich_mav(input_dir, output_dir)
    assert (output_dir / "mission" / "telemetry" / "imu.csv").exists()


def test_uavid_adapter_synthetic(tmp_path):
    input_dir = tmp_path / "raw"
    output_dir = tmp_path / "out"
    convert_uavid(input_dir, output_dir)
    assert (output_dir / "mission" / "semantics" / "classes.json").exists()


def test_h3d_adapter_synthetic(tmp_path):
    input_dir = tmp_path / "raw"
    output_dir = tmp_path / "out"
    convert_h3d(input_dir, output_dir)
    assert (output_dir / "mission" / "reference" / "dtm.tif").exists()
