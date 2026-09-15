# Phase 2: Camera Model, Calibration, Intrinsics Management

## 1. Audit of Existing Camera Handling

Before redesigning the camera layer, an audit of the current pipeline was conducted:

*   **Focal Length Estimation:** Focal length (`fx`, `fy`) is derived either directly from provided JSON (`meta["camera_intrinsics"]` or an `override` file) or estimated from `focal_length_mm`, `sensor_width_mm`, and `sensor_height_mm` in `schemas.py`.
*   **Principal Point:** If explicit `cx`/`cy` are provided, they are scaled. If estimating from sensor size, the principal point is hardcoded to precisely the center of the image (`width / 2`, `height / 2`).
*   **Skew:** Always assumed to be exactly zero.
*   **Distortion Handling:** Completely ignored. The current matrix `K` assumes a pure pinhole camera. No distortion coefficients are evaluated, passed to OpenCV, or provided to COLMAP.
*   **OpenCV/COLMAP Models:** `app/pipeline/colmap.py` rigidly passes `--ImageReader.camera_model PINHOLE`. The internal OpenCV pipeline relies on `findEssentialMat` and `triangulatePoints` without distortion mapping.
*   **Rescaling Imagery:** Imagery is rescaled during preprocessing (e.g., down to `960px` width) in `preprocess.py`.
*   **Intrinsics Rescaling:** `schemas.py:intrinsics()` scales `fx`, `fy`, `cx`, `cy` if explicitly supplied, or uses the target width/height directly when calculating from sensor size.
*   **Fixed Camera Matrix:** The pipeline calculates a single matrix `K` and uses it rigidly across all frames and stages (SfM, Dense, Mesh, Texture). Changing zoom or multi-camera flights are not supported.
*   **Texture Projection:** Assumes the same fixed pinhole `K` in the meshing/texturing stages.

## 2. Canonical Camera Data Structure

A new centralized `CameraModel` class will be implemented in `app/camera.py` representing:
*   Model type (e.g. `PINHOLE`, `SIMPLE_RADIAL`, `OPENCV`)
*   Dimensions (`width`, `height`, `original_width`, `original_height`)
*   Focal lengths (`fx`, `fy`)
*   Principal point (`cx`, `cy`)
*   Skew
*   Distortion coefficients
*   Calibration source & state

## 3. Resolution Scaling & Consistency

If frames are resized during `preprocess.py`, `CameraModel.scale(new_width, new_height)` will safely transition all internal properties (focal length and principal point).
Downstream code will query the camera for its active `K` matrix and OpenCV-compatible distortion array.

## 4. Undistortion Strategy

The pipeline will explicitly differentiate between original frames and undistorted frames.
A caching undistorter will provide fast remapping. Since SfM relies on valid epipolar geometry, the camera module will provide explicit undistortion mapping ensuring future stages (like SfM) operate on mathematically correct pinhole projections if required.

## 5. COLMAP & OpenCV Compatibility

The model will expose `.to_colmap()` and `.to_opencv()` methods to prevent scattering raw matrix assemblies across `runner.py`, `sfm.py`, and `colmap.py`.

## 6. Offline Calibration Utility

A new utility `scripts/calibrate_camera.py` will allow users to process checkerboard sequences and emit a valid `camera_intrinsics.json`.

## 7. Artifact Generation

The active camera configuration will be saved as `camera_model.json` to the job artifact directory and summarized in the API response.
