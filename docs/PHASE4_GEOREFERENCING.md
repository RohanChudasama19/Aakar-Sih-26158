# Phase 4 Georeferencing Audit

## Current Georeferencing Implementation

### GPS Parsing and Synchronization
- Reads `gps` dict from input, converts from WGS84 to local UTM via `pyproj`.
- Interpolates telemetry to video frames using the `frame` index, NOT timestamps.

### Sensor Usage
- **RTK/PPK**: Supports an optional `rtk.csv` which applies an interpolated offset (East, North, Up) to the UTM path.
- **Barometer**: Replaces GPS altitude completely via linear interpolation of `barometer.csv` if it exists.
- **IMU**: Ignored.

### Sim(3) Alignment
- Extracts SfM camera centers: `-R.T @ T`.
- Computes trajectory collinearity via SVD. Rejects alignment if trajectory is essentially a straight line or stationary point.
- Uses RANSAC (100 iterations) picking 4 random cameras at a time to solve Umeyama similarity transform `s, R, t`.
- Applies the final best-fit scale, rotation, and translation.

### Deficiencies
- **No Explicit Metric States**: `geo["valid"]` boolean is not expressive enough. It conflates metric scaling and georeferencing.
- **Timeline Alignment**: Uses arbitrary `frame` indices for interpolation, breaking if frame rates fluctuate or telemetry has gaps. Timestamp-based synchronization is required.
- **No Checkpoints**: Does not support separating independent checkpoints from alignment control points, thus it cannot compute true independent accuracy.
- **Coordinate System**: Uses UTM. A local Cartesian tangent plane like ENU (East-North-Up) is typically better for UAV flights to minimize projection distortions, although UTM is workable.
- **Transform Application**: Camera poses are not transformed into the world coordinate system, leaving them relative while the mesh/points are scaled.

## Required Architectural Changes
1. **Metric State Model**: Enforce states (`RELATIVE`, `METRIC_SCALE`, `GEOREFERENCED_METRIC`).
2. **Timestamp Sync**: Align telemetry to frames using explicit time mapping.
3. **Robust Alignment API**: Separate the similarity transform, returning explicit error budgets (Alignment Residual vs Checkpoint Accuracy).
4. **Transform Propagation**: Propagate the computed Sim(3) to the actual `CameraModel` poses before downstream processes consume them.
