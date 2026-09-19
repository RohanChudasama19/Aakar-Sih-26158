import pytest
import numpy as np
import json
from pathlib import Path


def test_rotation_matrix_sanity():
    # A valid rotation matrix
    theta = np.radians(30)
    R_valid = np.array([[np.cos(theta), -np.sin(theta), 0], [np.sin(theta), np.cos(theta), 0], [0, 0, 1]])
    assert np.isclose(np.linalg.det(R_valid), 1.0)
    err = np.linalg.norm(np.dot(R_valid.T, R_valid) - np.eye(3))
    assert err < 1e-6

    # An invalid matrix (e.g. intrinsic matrix from Zurich calibration)
    K_invalid = np.array([[893.39, 0.0, 951.13], [0.0, 898.32, 555.13], [0.0, 0.0, 1.0]])
    assert not np.isclose(np.linalg.det(K_invalid), 1.0)
    err_invalid = np.linalg.norm(np.dot(K_invalid.T, K_invalid) - np.eye(3))
    assert err_invalid > 1.0


def test_unknown_convention_handling(tmp_path):
    # Ensure that if IMU_FRAME_STATUS is UNKNOWN, fusion systems reject orientational calculations
    metadata = {"imu_orientation_convention": "UNKNOWN", "camera_optical_frame": "UNKNOWN"}
    meta_file = tmp_path / "flight_metadata.json"
    with open(meta_file, "w") as f:
        json.dump(metadata, f)

    with open(meta_file) as f:
        loaded = json.load(f)

    assert loaded["imu_orientation_convention"] == "UNKNOWN"

    def simulate_phase_e2_orientation_fusion(meta):
        if meta.get("imu_orientation_convention") == "UNKNOWN":
            raise ValueError("BLOCKED: Cannot fuse orientation with UNKNOWN frames.")
        return True

    with pytest.raises(ValueError, match="BLOCKED"):
        simulate_phase_e2_orientation_fusion(loaded)


def test_extrinsic_metadata_parsing(tmp_path):
    # Simulate missing extrinsics correctly flagging as NOT_AVAILABLE
    calib_file = tmp_path / "camera_imu_extrinsics.json"

    def load_extrinsics(path: Path):
        if not path.exists():
            return "NOT_AVAILABLE"
        return "AVAILABLE"

    assert load_extrinsics(calib_file) == "NOT_AVAILABLE"

    calib_file.write_text("{}")
    assert load_extrinsics(calib_file) == "AVAILABLE"
