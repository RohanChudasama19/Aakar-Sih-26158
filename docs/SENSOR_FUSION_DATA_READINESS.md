# Sensor Fusion Data Readiness

This report tracks the availability and verification status of genuine sensor data required for Phase E (Sensor Fusion) testing.

| Field | Zurich Urban MAV Status |
|-------|-------------------------|
| **RGB Images** | VERIFIED |
| **Frame Timestamps** | VERIFIED |
| **GPS** | VERIFIED |
| **IMU Accel Magnitude** | VERIFIED |
| **IMU Gyro Magnitude** | VERIFIED |
| **IMU Axes Convention** | UNKNOWN |
| **Camera Optical Frame** | UNKNOWN |
| **Camera-IMU Extrinsic Matrix** | NOT_AVAILABLE |
| **Quaternion Component Order** | VERIFIED (w,x,y,z) |
| **Quaternion Rotation Direction** | UNKNOWN |
| **Barometer** | VERIFIED |
| **RTK** | NOT_AVAILABLE |
| **Ground-Truth Translation Units** | VERIFIED (meters, UTM32N) |
| **Ground-Truth Orientation** | AVAILABLE_BUT_CONVENTION_UNKNOWN (Euler r/p/y) |
| **Intrinsics** | VERIFIED |
| **Absolute Timestamp** | NOT_AVAILABLE (Relative microseconds) |

*Note: MARS-LVIG requires a manual download by the user to bypass Google Drive limitations.*

### Phase E Safety Analysis
Because spatial conventions (IMU Axes, Camera-IMU extrinsics) are UNKNOWN or NOT_AVAILABLE, Phase E must be split:
- **Phase E1 (Safe Now):** Frame-agnostic sensor fusion (accel/gyro magnitudes, barometric relative altitude, GNSS position constraints).
- **Phase E2 (Blocked):** Orientation-dependent fusion (gravity alignment, body-to-camera rotation, quaternion pose fusion) is strictly BLOCKED until conventions are proven.
