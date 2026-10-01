import os

docs_dir = 'docs/heatmaps'
os.makedirs(docs_dir, exist_ok=True)

docs = {
    "ARCHITECTURE.md": """# Heatmap Architecture

## 1. Goal
Provide a non-destructive, scientifically grounded mechanism to visualize 3D metrics directly atop the accepted AAKAR reconstruction geometries in the Three.js viewer.

## 2. Components
- **Metrics Computation Engine**: Backend service interfacing with 	rimesh, 
umpy, and spatial indices (scipy.spatial.cKDTree) to evaluate geometry.
- **Artifact Generator**: Serializes numerical metrics separately from color ramps to allow dynamic client-side filtering.
- **Viewer Heatmap Layer**: A Three.js ShaderMaterial extension bridging the loaded numerical attributes to custom color gradients.

## 3. Strict Guarantees
- Original geometries are preserved.
- MARS coordinates remain relative.
- Colors derive purely from math, never aesthetic approximation.
""",
    
    "DATA_INVENTORY.md": """# Data Inventory

## 1. MARS (mars_hkairport01_quality)
- **Dense Cloud Path**: work/outputs/scene_dense.ply (AVAILABLE)
- **Mesh Path**: work/outputs/scene_mesh.ply (AVAILABLE)
- **Textured GLB Path**: work/outputs/representations/scene_textured.glb (AVAILABLE)
- **Registered Camera Model**: work/sparse/0/cameras.txt / images.txt (AVAILABLE)
- **Coordinate Frame**: Arbitrary local Euclidean (AVAILABLE)
- **Metric Scale**: RELATIVE
- **Independent Reference Data**: NOT_VERIFIED

## 2. Colorado
- **Dense Cloud Path**: work/outputs/scene_dense.ply (AVAILABLE)
- **Mesh Path**: MISSING (Degraded reconstruction)
- **Coordinate Frame**: Geo-registered UTM (AVAILABLE)
- **Metric Scale**: ABSOLUTE
- **Independent Reference Data**: NOT_VERIFIED
""",
    
    "COORDINATE_CONTRACT.md": """# Coordinate Contract

## Transformations
1. **COLMAP World**: Y-down, Z-forward relative to camera.
2. **Dense Cloud & Mesh**: Temporarily rotated during export (Z-up) for standard GIS interoperability.
3. **GLB Viewer Coordinates**: WebGL uses Y-up. The loader intrinsically maps GLB Z-up to WebGL Y-up.
4. **GPS/UTM Coordinates**: Valid strictly for Colorado (ABSOLUTE). MARS operates purely in local bounds.

## Restrictions
- Heatmap spatial indices must operate on the native scene_mesh.ply coordinate space before viewer-side orientation tricks.
- Z-values must never be blindly assumed as absolute elevation in RELATIVE datasets.
""",

    "METRIC_DEFINITIONS.md": """# Metric Definitions

## 1. Point Density
- **Definition**: Number of dense cloud vertices within a $ radius sphere of the query location.
- **Normalization**: Computed as volumetric density or projected surface density depending on local curvature.
- **Handling**: Boundary edges default to low density.

## 2. Surface Support
- **Definition**: Minimum Euclidean distance from a mesh face centroid to the nearest un-filtered dense cloud point.
- **Weak-support**: Faces with distances $> \epsilon$ are weak.

## 3. Camera Observations
- **Definition**: Number of verified camera frustums intersecting the query point.
- **Label**: POTENTIAL_CAMERA_VISIBILITY (since full occlusion raycasting across 7.5M points is computationally prohibitive in real-time).

## 4. Reconstruction Risk
- **Definition**: Boolean or scalar fusion of low surface support and low point density. 
- **Interpretation**: Not a substitute for geometric accuracy. It highlights interpolation vs observation.

## 5. Independent Geometric Error
- **Status**: GEOMETRIC_ERROR_AVAILABLE = FALSE for MARS. 
- **Condition**: Awaiting verified absolute ground control points (GCPs).
""",

    "ARTIFACT_SCHEMA.md": """# Artifact Schema

## Version 1.0 JSON Specification
`json
{
  "schema_version": 1,
  "mission_id": "mars_hkairport01_quality",
  "metric_name": "SURFACE_SUPPORT",
  "metric_units": "relative_distance",
  "coordinate_state": "RELATIVE",
  "mesh_hash": "sha256...",
  "scientific_limitations": "Does not equate to absolute volumetric truth.",
  "data": [
    0.0012, 0.0054, ... // ordered per-vertex or per-face
  ]
}
`
**Constraint**: Visualization palettes are NOT baked into the array.
""",

    "VIEWER_INTEGRATION.md": """# Viewer Integration

## 1. Architecture
- Extend AAKARViewer to load the .json numerical artifact asynchronously.
- Inject vertex colors using BufferAttribute('color') on the existing THREE.Mesh.

## 2. UI Contract
- Heatmaps function as an overlay toggle.
- Opacity sliders permit blending with the original textured material.
- Clicking a face retrieves the actual float value from the artifact array via raycast intersection index.

## 3. Safeguards
- Orbit/Walk/Fly states remain uninterrupted.
- Missing data renders as explicit magenta #FF00FF (invalid).
""",

    "SCIENTIFIC_LIMITATIONS.md": """# Scientific Limitations

1. **POTENTIAL_CAMERA_VISIBILITY**: This does not guarantee the camera successfully extracted photogrammetric features at the point.
2. **Surface Support**: Points might be dense noise. Proximity does not definitively prove sub-cm ground truth.
3. **No Cross-Mission Comparability**: A density of '50' in MARS has zero mathematical parity with a density of '50' in Colorado due to differing GSDs and RELATIVE vs ABSOLUTE scaling.
""",

    "IMPLEMENTATION_PLAN.md": """# Implementation Plan (Phase 2)

1. **Backend Generators**: Develop python scripts utilizing scipy.spatial.cKDTree for support and density over scene_mesh.ply.
2. **Artifact Endpoints**: Serve GET /api/jobs/{jid}/heatmaps/{metric}.
3. **Frontend Loader**: Implement THREE.FileLoader for JSON ingestion.
4. **Shader Injection**: Construct HeatmapMaterial inheriting physical attributes but replacing albedo with gradient lookup.
5. **UI Integration**: Mount toolbar buttons for toggle states and color legends.
"""
}

for filename, content in docs.items():
    path = os.path.join(docs_dir, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print("Documentation generated.")
