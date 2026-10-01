# Phase 2 Completion Report

## 1. Objectives Addressed
Phase 2 focused on creating a robust, unified, and traceable Camera Model to handle intrinsically calibrated geometries and lens distortion natively.

## 2. Work Completed
1. **Canonical `CameraModel` (`app/camera.py`)**:
    - Centralized implementation handling PINHOLE, RADIAL, and OPENCV models.
    - Enforces scale and crop operations without breaking geometry relationships.
    - Computes `to_matrix()` and `to_colmap()` unambiguously.
    - Classifies source metadata via `CalibrationSource` (e.g. `PROVIDED_CALIBRATION` vs `METADATA_DERIVED`).

2. **Undistortion Layer (`Undistorter`)**:
    - Explicitly applies polynomial distortion un-mapping natively via OpenCV (`initUndistortRectifyMap` and `remap`).
    - Exposes `get_undistorted_camera()` to compute the exact downstream matrix needed for zero-distortion solvers.

3. **Pipeline Integration (`app/pipeline/runner.py`)**:
    - Pre-computed extracted frames (`work / frames`) and uncropped versions (`work / originals`) are now routed through the `Undistorter`.
    - If distortion exists, the pipeline transparently creates `work / undistorted_frames` and `work / undistorted_originals`.
    - Downstream steps (`sfm.reconstruct`, `colmap.sparse`, `dense.densify`) simply process the clean images using the correctly updated `CameraModel`.
    - Exposes a new job artifact: `camera_model.json`.

4. **Offline Calibration (`scripts/calibrate_camera.py`)**:
    - Utility script added for processing folder paths containing standard checkerboards.
    - Computes focal lengths, principal points, and distortion parameters for PINHOLE, RADIAL, or full OPENCV models.
    - Exports directly to the standard `camera_intrinsics.json` format used by the AAKAR ingest endpoints.

5. **Test Coverage (`tests/test_camera.py`)**:
    - Complete suite for geometric bounds checking, sub-pixel image coordinate scaling, non-uniform resolution adaptations, and OpenCV/COLMAP parameter serializers.

## 3. Results & Next Steps
- The Phase 2 model preserves the previous functional metrics while adding rigorous mathematical structures for handling lenses safely.
- Code cleanliness is enforced via MyPy typing (`CameraModel` vs raw `np.ndarray` 3x3s).
- Next target is **Phase 3: Robust Structure-from-Motion (SfM) Initialization**.
