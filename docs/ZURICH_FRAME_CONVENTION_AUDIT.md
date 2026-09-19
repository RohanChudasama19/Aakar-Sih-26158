# Zurich MAV Frame Convention Audit

## Phase D2 Closure & Pre-Flight Audit

This document establishes the verified state of coordinate frames and sensor units for the `AGZ_subset` of the Zurich Urban MAV dataset. Do NOT guess conventions if they are not mathematically or textually provable.

### 1. Extrinsic Matrix Audit
Inspecting `calibration_data.npz`:
- **Array Name:** `intrinsic_matrix`
- **Dimensions:** 3x3
- **Numerical Type:** `float64`
- **Source Documentation:** `readme.txt` ("internal camera parameters computed using the images from './AGZ/MAV Images Calib/'")
- **Intended Frames:** Camera sensor frame (pixels)
- **Matrix Type:** Intrinsic Camera Matrix ($K$)
- **Units:** Pixels
- **Sanity Check:** Not a rotation matrix ($det(K) = 802555.996616$, $R^T R$ error = $2.16 \times 10^6$).

- **Array Name:** `distCoeff`
- **Dimensions:** 1x5
- **Numerical Type:** `float64`
- **Matrix Type:** Distortion coefficients

**NOTE:** There is NO `camera_imu_extrinsics` matrix in `calibration_data.npz` or `write_ros_bag.py`.

### 2. Status per Item

| Property | Status | Value | Evidence | Safe for Phase E? |
| :--- | :--- | :--- | :--- | :--- |
| IMU Axes (`RawAccel`, `RawGyro`) | UNKNOWN | N/A | Z is approx -10.58 m/s^2 at rest, implying NED, but unproven. | NO |
| Camera Optical Frame | UNKNOWN | N/A | No documentation found. | NO |
| World/Local Frame Convention | VERIFIED | UTM Zone 32N | `readme.txt` states `GroundTruthAGL.csv` uses WGS 84 / UTM 32N. | YES (for GT) |
| Pose Transform Direction | UNKNOWN | N/A | No documentation found. | NO |
| Quaternion Component Order | VERIFIED | `w, x, y, z` | `OnboardPose.csv` headers explicitly state `Attitude_w, Attitude_x, Attitude_y, Attitude_z`. | YES |
| Quaternion Rotation Direction | UNKNOWN | N/A | Unstated whether world->body or body->world. | NO |
| Camera-IMU Extrinsic Matrix | NOT_AVAILABLE | N/A | Missing from `calibration_data.npz` and `readme.txt`. | NO |
| Extrinsic Transform Direction | NOT_AVAILABLE | N/A | N/A | NO |
| Translation Units (GroundTruth) | VERIFIED | meters | UTM Zone 32N coordinates are inherently metric. | YES |
| Translation Units (OnboardPose) | UNKNOWN | N/A | Implied meters (`Altitude=474.8`), but unproven. | NO |
| Accel Units (`RawAccel`) | VERIFIED | m/s^2 | Matches gravity magnitude (~9.8 - 10.6). | YES (Magnitude) |
| Gyro Units (`RawGyro`) | VERIFIED | rad/s | `readme.txt` lists column as `range_rad_s`. | YES (Magnitude) |
| Barometer Units | VERIFIED | hPa | Pressure reads ~957.8 at 471m, standard atmospheric model. | YES |
| Extrinsics match dataset | NOT_AVAILABLE | N/A | Extrinsics do not exist. | NO |

### 3. Pose File Audit
**`OnboardPose.csv`** (Do NOT mix with Ground Truth):
Contains `Timpstemp`, angular rates (`Omega_xyz`), filtered acceleration (`Accel_xyz`), velocity (`Vel_xyz`), accelerometer bias, azimuth, attitude quaternion (`w,x,y,z`), height, altitude, and Pixhawk tether data. Frame conventions UNKNOWN.

**`GroundTruthAGL.csv`** (Reference Evaluation Only):
Contains image ID, translation (`x_gt`, `y_gt`, `z_gt` in UTM 32N meters), and Euler angles (`omega_gt` yaw, `phi_gt` pitch, `kappa_gt` roll in degrees). Contains independent GPS measurements.

### 4. Phase E Safety Gate
**SAFE NOW (Phase E1: Frame-Agnostic):**
- Accelerometer magnitude analysis (m/s^2)
- Gyroscope magnitude analysis (rad/s)
- Relative barometric trend (hPa to relative altitude)
- Timestamp-aligned pose translation comparison (distance scalar)
- GNSS position constraints (WGS84 / UTM)

**NOT SAFE YET (Phase E2: Orientation-Dependent):**
- Gravity alignment
- Orientation prior injection
- Camera attitude regularization
- Body-to-camera rotation mapping
- Quaternion pose fusion
