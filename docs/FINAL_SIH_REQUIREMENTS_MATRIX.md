# Phase N/O/P Semantic Dynamic Masking Closure Report

## Model Provenance Error Corrected
The previous experiment used a corrupted/early epoch-0 checkpoint (hash 42497ac9). We have transparently discarded that result. 
The pipeline was subsequently re-run via the verified training script to produce a valid `best_model.pth` (epoch 2, hash 92153426) which achieved a validation mIoU of 0.3138.

## Dynamic A/B Results
With the newly verified trained ONNX model (hash b1bd7327):
- **Moving Car Detection**: The model (due to limited early-stopping epochs) achieved only a 0.003 IoU for the `Moving Car` class.
- **Consequence**: The dynamic masking pipeline failed to identify the vast majority of moving vehicles in `seq18`.
- **Result**: `REAL_DYNAMIC_MASKING_EFFECT = INCONCLUSIVE` because dynamic artifacts (ghosting) remained virtually identical to the baseline.
- **Status**: Dynamic masking remains `OPTIONAL_EXPERIMENTAL` and defaults to `OFF`.

## 2D-to-3D Projection
- **Coverage**: 100% of dense points labeled (mean confidence: 0.81).
- **Artifacts**: `semantic_mesh.ply` and `semantic_labels.npz` load successfully in Semantic and Confidence viewer modes.
