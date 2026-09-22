# Phase N/O/P2 Semantic Dynamic Masking Report

## Real Before/After Evidence
An A/B test was performed on UAVid `val/seq18`, containing significant `Moving Car` content.

- **Baseline**: Static scene successfully mapped, but significant ghost trails around moving cars were observed.
- **Masked**: Semantic masks successfully stripped features in dynamic regions (`FEATURE_MASK_CONSUMED = TRUE`). However, because the semantic ONNX model is insufficiently tuned, it over-masked static geometry (Road edges).
- **Result**: `REAL_DYNAMIC_MASKING_EFFECT = NO_MEASURED_IMPROVEMENT` due to unacceptable static-scene degradation.

## 2D-to-3D Projection
- **Coverage**: 100% of dense points labeled.
- **Mean Confidence**: 0.88.
- **Artifact**: `semantic_mesh.ply` generated and verified.
