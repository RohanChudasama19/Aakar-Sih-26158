# Heatmap Architecture

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
