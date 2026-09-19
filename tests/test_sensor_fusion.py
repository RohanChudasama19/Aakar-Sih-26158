
import numpy as np
import pytest

from app.pipeline.sensor_fusion import (
    FusionStatus,
    GNSSQuality,
    PhaseE1Fusion,
    PositionPrior,
    check_orientation_fusion_safety,
    compute_sigma,
    fuse_orientation,
    parse_gnss_quality,
    pressure_to_relative_altitude,
    robust_position_alignment,
)


def test_gnss_prior_construction_and_uncertainty():
    q = parse_gnss_quality("RTK_FIXED")
    assert q == GNSSQuality.RTK_FIXED
    sx, sy, sz = compute_sigma(q, None, None, None)
    assert sx == 0.02
    assert sz == 0.03

    # Zero-sigma clipping
    sx, sy, sz = compute_sigma(GNSSQuality.UNKNOWN, 0.0, 0.0, 0.0)
    assert sx == 0.001


def test_robust_outlier_rejection():
    t = np.linspace(0, 10, 10)
    visual = np.column_stack([t, t * 0, t * 0])

    gnss_dst = np.column_stack([t, t * 0, t * 0])
    gnss_dst[5] = [5.0, 100.0, 0.0]

    priors = [
        PositionPrior(i, p[0], p[1], p[2], GNSSQuality.RTK_FIXED, 0.02, 0.02, 0.03, "gnss")
        for i, p in enumerate(gnss_dst)
    ]

    T, stats = robust_position_alignment(visual, priors, inlier_threshold=2.0)
    assert stats["total_priors"] == 10
    assert stats["rejected_priors"] == 1
    assert stats["used_priors"] == 9
    assert stats["median_residual"] < 1e-5


def test_barometer_math():
    alt = pressure_to_relative_altitude(957.8, 1013.25)
    assert 460 < alt < 480
    assert pressure_to_relative_altitude(1013.25, 1013.25) == 0.0


def test_orientation_fusion_blocked():
    meta = {"imu_orientation_convention": "UNKNOWN"}
    assert check_orientation_fusion_safety(meta) == FusionStatus.BLOCKED_FRAME_UNKNOWN

    meta = {"imu_orientation_convention": "NED"}
    assert check_orientation_fusion_safety(meta) == FusionStatus.BLOCKED_EXTRINSIC_MISSING

    with pytest.raises(ValueError, match="BLOCKED"):
        fuse_orientation()


def test_phase_e1_fusion_integration():
    fusion = PhaseE1Fusion({"imu_orientation_convention": "UNKNOWN"})

    assert fusion.report["fusion_status"]["gnss"] == FusionStatus.MISSING_DATA.value

    mq = fusion.process_frame(
        {
            "accel_x": 0.0,
            "accel_y": 0.0,
            "accel_z": -15.0,
            "gyro_x": 0.0,
            "gyro_y": 1.5,
            "gyro_z": 0.0,
            "pressure": 957.8,
        }
    )

    assert mq["high_acceleration"]
    assert mq["rapid_rotation"]
    assert mq["blur_risk"] in ["MEDIUM", "HIGH"]
    assert fusion.report["fusion_status"]["accel_magnitude"] == FusionStatus.ACTIVE.value
    assert fusion.report["fusion_status"]["gyro_magnitude"] == FusionStatus.ACTIVE.value
    assert fusion.report["fusion_status"]["barometer"] == FusionStatus.ACTIVE.value

    fusion.add_gnss_measurement(1.0, 10.0, 20.0, 30.0, "RTK_FLOAT")
    fusion.add_gnss_measurement(2.0, 11.0, 20.0, 30.0, "RTK_FLOAT")

    fusion.finalize()
    assert fusion.report["fusion_status"]["gnss"] == FusionStatus.ACTIVE.value
    assert fusion.report["gnss_statistics"]["total_priors_extracted"] == 2


def test_ground_truth_leakage_protection():
    fusion = PhaseE1Fusion({})
    assert len(fusion.gnss_priors) == 0
