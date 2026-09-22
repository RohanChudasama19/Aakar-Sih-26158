# Semantic Model Architecture

AeroRecon integrates a real optional semantic model backend, overriding the purely geometric heuristics where enabled.

## Architecture
- **Model**: LRASPP MobileNetV3-Large
- **Source**: PyTorch / Torchvision
- **Execution**: ONNX Runtime (CPU/CUDA)
- **Status**: IMPLEMENTED (Model Segmentation fallback gracefully degrades to Heuristic Fallback if weights are missing).

## Class Mapping
AeroRecon natively adopts the UAVid taxonomy and projects it to the internal unified types:
- Building -> BUILDING
- Road -> ROAD
- Tree / LowVegetation -> VEGETATION
- StaticCar -> OBSTACLE
- MovingCar / Human -> DYNAMIC_OBJECT
- Clutter -> UNKNOWN
