# Phase N/O/P: Real Semantic Segmentation + Dynamic Masking

## Objective
Implement a genuine semantic AI backbone (PyTorch -> ONNX) capable of overriding the baseline heuristics, trained on UAVid. Integrate dynamic masks into feature extraction and dense reconstruction.

## Status Summary
- **Implementation**: COMPLETE (ONNX Runtime inference, PyTorch training scripts, 2D->3D visibility projection, multi-view fusion, `preprocess.py` mask integration).
- **Synthetically Tested**: VERIFIED (Pipeline fallback, class mappings, 2D->3D logic, PyTorch-ONNX numerical agreement verified via pytest / stub tests).
- **Real-Data Validated**: NOT_AVAILABLE. (The `data_external/uavid/raw` dataset is currently missing, and PyTorch CUDA is unavailable on the testbed. Real UAVid model training is suspended pending data).

## Integrations
- `preprocess.py` actively intercepts `SemanticPipeline` output and writes out feature masks.
- `sfm_backend.py` instructs COLMAP to consume these masks.
- `HEURISTIC_FALLBACK` seamlessly takes over when ONNX models are absent.
