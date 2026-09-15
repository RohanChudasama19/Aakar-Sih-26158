# Phase 7: Semantics

## Audit of Existing Semantics
- **Heuristics**: Current logic in `app/pipeline/semantic.py` uses naive color/height heuristics directly on 3D points. Vegetation is detected by `G > R * 1.12 & G > B * 1.07`. Buildings by `Z > 10th percentile Z + 2m`. Neutral color for roads. Dark points as unknown.
- **YOLO / Segmentation Usage**: None present in semantic pipeline. Dynamic masking in `preprocess.py` exists (e.g. YOLOv8) but isn't integrated into building/road 3D semantics.
- **Class Mappings**: Existing: `terrain_candidate`, `building_candidate`, `road_candidate`, `vegetation_candidate`, `unknown`.
- **Confidence Values**: Currently does not exist. Hard assignments only.
- **Projection Logic**: Existing approach uses 3D `cKDTree` nearest neighbor from points to face centroids. No multi-view projection logic.
- **UI Integration**: Point fractions and relative surface areas computed for JSON.
- **Limitations**: Inaccurate, no geometric context, no ML segmentation support, no bounds for water or infrastructure. No image-space evidence fusion or occlusion handling.

## New Architecture

### SemanticBackend Abstraction
1. `HeuristicSemanticBackend`: Fallback that extends current heuristics but maps correctly to the required classes and computes synthetic confidences to fit the interface.
2. `ModelSemanticBackend`: Image-based ML semantic segmentation fused into 3D. 

### Multi-View Semantic Fusion
For model-based semantics, predictions are generated in image space. A projection step calculates:
- Camera visibility (occlusion raycasting).
- View angle weighting.
- Image resolution weighting.
- Confidence-weighted voting per mesh face.

### Classes
- `BUILDING` (Subclasses: `ROOF`, `FACADE` mapped structurally)
- `ROAD`
- `GROUND`
- `VEGETATION`
- `WATER`
- `INFRASTRUCTURE`
- `OBSTACLE`
- `UNKNOWN`

### Boundaries and Structure
- Semantic smoothing respects geometric discontinuities (e.g., sharp normals, boundaries).
- Connected component analysis clusters `BUILDING` and extracts structural footprints.

### Export
- `semantic_labels.npz`, `semantic_mesh.ply`
- `semantic_report.json`
