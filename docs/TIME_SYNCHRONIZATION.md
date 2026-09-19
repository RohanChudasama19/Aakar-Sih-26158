# Phase D: Time Synchronization

## Architecture
The canonical sensor time synchronization layer (`app/pipeline/time_sync.py`) maps disparate input streams (GPS, IMU, Barometer, etc.) into a consistent, monotonic, and interpolated temporal frame aligned with the video/image sequences.

### Interpolation Policies
- **GPS / RTK**: Coordinates are projected into ECEF metric Cartesian space, linearly interpolated, and reprojected to Geodetic.
- **Accelerometer / Gyroscope / Barometer**: Strict linear interpolation.
- **Orientation (Quaternion)**: Spherical Linear Interpolation (SLERP) ensuring shortest-path and normalized outputs.
- **Extrapolation**: Explicitly disabled (`OUTSIDE_SENSOR_RANGE`).
- **Gap Enforcement**: Configurable thresholds per stream reject interpolation across missing data.

### Duplicate & Monotonicity Handling
Out-of-order timestamps are sorted into monotonicity. Duplicate timestamps are handled deterministically via `KEEP_FIRST` policy by default, ensuring downstream filters receive predictable inputs without raw data deletion.
