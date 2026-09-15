# Phase 3 SfM Audit

## Current SFM Implementation

### CPU Fallback (`app/pipeline/sfm.py`)
- **Feature Detector**: OpenCV SIFT (`cv2.SIFT_create(nfeatures=5000)`).
- **Descriptor**: SIFT.
- **Matching Strategy**: Exhaustive sequential matching over a sliding window (frame $a$ to frames $a+1 \dots a+7$). Brute-force KnnMatch (k=2) with Lowe's ratio test (0.72 threshold).
- **RANSAC / Geometric Verification**: `cv2.findEssentialMat` with RANSAC (prob=0.999, threshold=1.0) and `cv2.recoverPose`.
- **Initialization Logic**: Evaluates all valid pairs in the sliding window and picks the pair with the most geometrically verified inliers (triangulated points that pass angle/depth checks).
- **Camera Registration**: Iterative PnP. Searches for candidate 2D-3D matches from already registered frames. Uses `cv2.solvePnPRansac` (EPnP, 300 iterations) followed by `cv2.solvePnPRefineLM`.
- **Triangulation**: Standard OpenCV `cv2.triangulatePoints`. Validates positive depth, minimum triangulation angle (0.7° to 80°), and reprojection error (< 2.5px).
- **Bundle Adjustment**: **Absent**. PnP LM only refines the newly added camera pose locally. Points and existing cameras are never globally optimized.
- **Outlier Filtering**: Strict thresholding on reprojection and track geometry. Points are not filtered post-triangulation.
- **Format**: Dictionary mapping indices to `np.ndarray` poses, and a list of 3D points.
- **Known Failures**: Lacks global loop closure, suffers drift over long sequences due to missing global Bundle Adjustment, does not scale efficiently to large datasets.

### COLMAP Backend (`app/pipeline/colmap.py`)
- **Feature Detector / Descriptor**: COLMAP SIFT (GPU accelerated via CUDA).
- **Matching Strategy**: `sequential_matcher` with fixed overlap (10 frames).
- **Geometric Verification**: Handled internally by COLMAP during matching.
- **Initialization**: Handled internally by COLMAP mapper.
- **Camera Registration / Triangulation**: Incremental COLMAP mapper.
- **Bundle Adjustment**: Built-in COLMAP incremental bundle adjustment (Ceres). Focal length, principal point, and extra params refinement are hard-disabled (`--Mapper.ba_refine_* 0`).
- **Outlier Filtering**: Handled internally by COLMAP mapper.
- **Integration**: Executes via `subprocess.run` calling CLI binaries (`feature_extractor`, `sequential_matcher`, `mapper`, `model_converter`).
- **Format**: Reads `images.txt` and `points3D.txt` to extract `points`, `colors`, `poses`.
- **Known Limitations**: Hardcoded to `sequential_matcher` (no spatial loops) and `mapper` (incremental only). Fails ungracefully if COLMAP binary is missing or GPU is disabled. Does not leverage focal priors or calibration confidence appropriately. No handling for multiple models (just picks the largest).

## Required Architecture Changes
1. **SfM Backend Abstraction**: We need an `SfMBackend` interface wrapping `COLMAP_SFM` and `CPU_FALLBACK_SFM`.
2. **Adaptive Matching**: Sequential matching must be adaptive based on telemetry and Phase 1 metrics (not hardcoded to 10 frames).
3. **Mapper Strategy**: Enable `GLOBAL` and `HIERARCHICAL` modes dynamically for larger missions.
4. **Bundle Adjustment Refinement**: We must selectively enable focal refinement if calibration is estimated, but lock it if calibrated.
5. **Caspar Support**: Integrate COLMAP 4.1 Caspar GPU BA where available.
6. **Detailed Reporting**: Parse COLMAP output or logs to provide `sfm_report.json` with metrics (track lengths, triangulation angles, BA cost).
7. **Graceful Fallback**: Detect CUDA/COLMAP capability and explicitly route to CPU fallback if required, while recording the reason.
