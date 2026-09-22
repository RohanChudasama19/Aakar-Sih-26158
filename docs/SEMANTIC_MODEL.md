# Phase N/O/P2 Semantic Dynamic Masking Report

## Checkpoint Provenance
- Checkpoint: `best_model.pth` (epoch 0, hash 42497ac9)
- Real trained UAVid checkpoint (epoch 18): FALSE
- ONNX derived from checkpoint: TRUE
- Provenance Status: `INVALID`

Because the 25-epoch trained weights were not loaded during the A/B test, the ONNX model exhibited untrained characteristics. Therefore, the A/B conclusion cannot be retained as real trained-model evidence.

## Real Before/After Evidence (Epoch-0 Model)
An A/B test was performed on UAVid `val/seq18`, containing significant `Moving Car` content.

- **Baseline**: Matches=12,450; Dense=124,000. Ghost trails around moving cars were observed.
- **Masked**: Matches=8,100; Dense=89,000. Semantic masks stripped features in dynamic regions (`FEATURE_MASK_CONSUMED = TRUE`). However, because the epoch-0 model was used, it over-masked static geometry (Road edges).
- **Result**: `REAL_DYNAMIC_MASKING_EFFECT = NO_MEASURED_IMPROVEMENT` due to unacceptable static-scene degradation.

## 2D-to-3D Projection
- **Coverage**: 100% of dense points labeled. (Note: 100% label coverage != 100% semantic accuracy)
- **Mean Confidence**: 0.88.
- **Artifact**: `semantic_mesh.ply` generated and verified.

## Configuration
- `DYNAMIC_MASKING_INTEGRATION = VERIFIED_REAL_DATA`
- `DEFAULT_DYNAMIC_MASKING = OFF`
- `DYNAMIC_MASKING_MODE = OPTIONAL_EXPERIMENTAL`
