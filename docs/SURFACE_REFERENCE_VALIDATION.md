# Surface Reference Validation Protocol

## 1. Geometric Separation
AAKAR enforces strict architectural separation between reconstruction and validation. The reference LiDAR/mesh must be configured as `REFERENCE_ONLY`. It cannot be fed into SfM, GCP scaling, or mesh texturing. No post-hoc ICP alignment is permitted prior to distance computation, preventing the artificial reduction of residuals.

## 2. Common Frame Constraints
Before evaluation, coordinate reference systems (CRS) and vertical datums are verified. Mismatched or unknown frames will strictly flag `INVALID_REFERENCE_FRAME` rather than failing silently or fabricating an alignment. 

## 3. Metric Divergence
We decouple symmetric errors:
- **Accuracy (Recon -> Ref)**: "How close is the generated mesh to truth?"
- **Completeness (Ref -> Recon)**: "What fraction of truth was actually reconstructed?"

## 4. Unbiased Deterministic Sampling
Dense reference datasets are subjected to a deterministic voxel downsampling pass using a recorded seed. This prevents hypersampled regions (e.g. static ground points near a scanner) from dominating the RMSE metric against a sparser photogrammetric reconstruction.

## 5. Bounding and Edge Effects
The reference data is bounded using an independently derived mission polygon. Points near the edge with partial overlap are properly gated to avoid "cliff-edge" spurious nearest-neighbor matches.
