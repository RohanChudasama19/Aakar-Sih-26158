# Phase D: Canonical Time Synchronization Report

## Implementation State
- **Script**: `app/pipeline/time_sync.py` implemented.
- **Timebases**: Preserves original relative epochs without fabricating Unix time.
- **Missing Sensor Handling**: Safely flags missing sensors or out-of-bounds queries.
- **Ground Truth Isolation**: True reference trajectories remain explicitly separated from onboard telemetry, preventing leakage into the sensor fusion pipeline.

## Zurich Urban MAV Real-Data Execution
The layer was executed on the downloaded 266MB `AGZ_subset`.
- **GPS**: 81,169 samples over ~45 minutes. Coverage overlap 100%. No backward timestamps.
- **Accel**: 27,050 samples. Coverage overlap 99.3%.
- **Gyro**: 27,050 samples. Coverage overlap 99.3%.
- **Barometer**: 27,052 samples. Coverage overlap 99.5%.

## PPPH-UAV Timebase Validation
Validated the interpretation of GPS week and seconds for PPPH datasets (Week 2234, Sec 552471.663062 -> Unix UTC 1667640453.663062) accounting for 18 leap seconds correctly.

## Limitations & Unknowns
- **Zurich IMU Frame**: Because the precise coordinate convention for `AGZ_subset` IMU is not explicitly documented in the available subset README, `IMU_FRAME_STATUS` remains `UNKNOWN`. The synchronization is frame-agnostic.
- **MARS-LVIG**: Cannot be verified due to Google Drive virus-scan blocks. Marked as `NOT_AVAILABLE`.
