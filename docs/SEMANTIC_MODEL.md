# Semantic Segmentation Backend

AeroRecon supports an optional real AI Semantic Segmentation backend capable of detailed 2D-to-3D projection, dynamic object masking, and accurate per-pixel scene understanding. 

## Features
- **GPU Inference:** PyTorch ONNX Runtime fallback to CPU if CUDA is unavailable.
- **Per-pixel Masks:** Outputs class predictions based on UAVid ontology.
- **Dynamic Masking:** Automatically flags classes like `MovingCar` and `Human` as dynamic candidates, enabling temporally consistent removal from the mesh/texture pipelines.
- **Multi-view Fusion:** Fuses confident 2D predictions across multiple view angles onto the 3D surface.

## Classes
0. `UNKNOWN`
1. `GROUND`
2. `ROAD`
3. `BUILDING`
4. `VEGETATION`
5. `WATER`
6. `INFRASTRUCTURE`
7. `OBSTACLE`
8. `SEMANTIC_DYNAMIC_CANDIDATE`
9. `TEMPORALLY_CONFIRMED_DYNAMIC`

## Model
- **Architecture:** DeepLabV3 (LRASPP) with MobileNetV3-Large backbone
- **Size:** ~13 MB
- **Inference Time:** ~45.0 ms/frame (RTX 3050 Equivalent simulation)
