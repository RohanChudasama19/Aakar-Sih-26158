# Phase N/O/P: Real Semantic Segmentation + Dynamic Masking

## Objective
Implement a genuine semantic AI backbone (PyTorch -> ONNX) capable of overriding the baseline heuristics, trained on UAVid.

## Status
- **Implementation**: COMPLETE (ONNX Runtime inference, PyTorch training scripts, 2D->3D visibility projection, multi-view fusion).
- **Real UAVid Data**: NOT_AVAILABLE.
- **Real Model Validation**: NOT_AVAILABLE.
- **Numerical Agreement (PyTorch vs ONNX)**: VERIFIED (Max absolute difference: < 1e-5).

## Outcomes
The system exposes a flexible API capable of switching seamlessly between `MODEL_SEGMENTATION` and `HEURISTIC_FALLBACK` depending on ONNX weight availability and VRAM limits.
