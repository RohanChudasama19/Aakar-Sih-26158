# Phase 5: Dense Reconstruction

## Current Dense Implementation Audit
- **Path**: `app/pipeline/dense.py` handles dense stereo.
- **SGBM Usage**: Uses OpenCV `cv2.StereoSGBM_create`, configured strictly for horizontal positive disparity searches (`p2[0,3] < 0`).
- **Optical-Flow**: Fuses stereo with tracked feature matching via `cv2.calcOpticalFlowPyrLK` as a secondary geometry source.
- **COLMAP PatchMatch**: Not currently implemented.
- **OpenMVS**: Not implemented.
- **Source-View Selection**: Simply forms pairs linearly (`ids` array, `ids` vs `ids[2:]` and `ids[1:]`), capping at `max_pairs=12` regardless of geometric overlap.
- **Fusion Implementation**: Fuses points by concatenating numpy arrays.
- **Point Filtering**: Applies a rudimentary radius outlier filter (points must be within 2x the 95th percentile radius of the sparse cloud median). Grids points to remove duplicates using simple voxel downsampling.
- **GPU Behavior**: None. Strictly CPU using OpenCV arrays.
- **CPU Fallback**: This is the current implementation.
- **Existing Dense Artifacts**: Only outputs `xyz` and `rgb` which are passed directly to meshing, bypassing intermediate disk storage or report artifacts.
- **Failures/Limitations**: Will produce sparse patches due to bounded `max_pairs`, poor source-view selection logic without geometric overlap validation, and weak edge preservation via basic SGBM smoothing.

## Planned Changes
1. **Backend Abstraction**: Create `app/pipeline/dense_backend.py`. Define `DenseBackend` supporting `COLMAP_PATCHMATCH` and `CPU_FALLBACK`.
2. **COLMAP PatchMatch Implementation**: 
   - Integrate `colmap patch_match_stereo` and `colmap stereo_fusion`.
   - Setup an undistorted workspace utilizing the `camera_model` explicitly generated in Phase 2.
   - Extract depth maps and normal maps from COLMAP's `.photometric.bin` or `.geometric.bin` formats.
3. **Processing Profiles**: Define `FAST`, `BALANCED`, and `QUALITY` profiles that configure Max Image Size, Source Image Count, and Geometric Consistency toggles.
4. **Source Selection & Hardware Scaling**: Integrate bounds based on profile, scaling down dynamically for Large Missions.
5. **Dense Filtering**: Formalize statistical outlier removal (e.g. Open3D SOR or similar distance-based routines).
6. **Metric Integrity**: Ensure Dense points generated relative to the `SfM` workspace are perfectly scaled via Phase 4's Metric State transform before outputting `dense_metric.ply`.
