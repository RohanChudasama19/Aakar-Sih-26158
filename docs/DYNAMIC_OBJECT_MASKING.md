# Dynamic Object Masking

AeroRecon's semantic pipeline isolates `MovingCar` and `Human` as `SEMANTIC_DYNAMIC_CANDIDATE`. 

## Integration
The semantic pipeline (`SemanticPipeline`) is formally integrated into `app/pipeline/preprocess.py`.
- **Feature Extraction Masking**: Dynamic masks are written to `work/masks` and automatically consumed by COLMAP's `feature_extractor` via the `--ImageReader.mask_path` argument.
- **Dense/Texture Masking**: Undistorted images automatically inherit the zeroed-out dynamic masks, gracefully excluding moving objects from the dense point cloud and multi-view texturing.

## Temporal Confirmation
To prevent false-positive masking of static objects (e.g. parked cars falsely identified as moving), dynamic candidates undergo multi-frame temporal confirmation using optical flow or epipolar constraints. Once confirmed, they are elevated to `TEMPORALLY_CONFIRMED_DYNAMIC`.
