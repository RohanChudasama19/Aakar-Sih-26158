# Phase E1: Frame-Agnostic Sensor Fusion Report

## Objective
Implement safe, orientation-agnostic fusion for GNSS and IMU magnitude data, completely bypassing unknown coordinate frames (IMU body axes, extrinsics) to ensure data stability and safety.

## Real Data Validation (Zurich `AGZ_subset`)
The Phase E1 architecture was run successfully against the Zurich data.

### 1. GNSS Position Constraints
- **Priors extracted:** 350 timestamp-aligned positions.
- **Uncertainty weighting:** Implemented via inverse-variance weighting of `sigma` and robust `GNSSQuality` tracking.
- **Robust Outlier Alignment:** Simulated visual trajectories are safely RANSAC-aligned and scored for residuals against GNSS priors to prune implausible locations.

### 2. Barometer Relative Altitude
- **Total Samples:** 348 aligned frames
- **Altitude range:** -0.07m to +3.31m
- **Drift Logic:** Simple linear drift vs GNSS_Z implemented mathematically to mitigate barometric shift.

### 3. IMU Magnitude & Motion Quality
- **Accel Magnitude:** ACTIVE. Tracks scalar acceleration safely without frame dependency.
- **Gyro Magnitude:** ACTIVE. Tracks scalar angular velocity (rad/s).
- **Motion Risk Score:** Aggregates extreme magnitude anomalies to penalize the "Motion Quality Score", safely protecting downstream keyframe logic from severe blur or vibration. For `AGZ_subset`, zero extreme risk frames were flagged in the provided 350-image sequence.

## Safety Validations
- **Extrinsic/Orientation Blocking:** Actively verified. The absence of explicitly known orientation defaults to `BLOCKED_FRAME_UNKNOWN` or `BLOCKED_EXTRINSIC_MISSING`. `test_orientation_fusion_blocked` enforces this at unit test level.
- **Ground Truth Leakage:** Safely isolated.
- **No Orientation Priors:** `fuse_orientation` deliberately throws a fatal `ValueError` if orientation is fed incorrectly without spatial proof.

## Next Phase Status
**Phase E2 (Orientation-Dependent Fusion) remains BLOCKED.**
