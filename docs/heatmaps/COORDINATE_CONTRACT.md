# Coordinate Contract

## Transformations
1. **COLMAP World**: Y-down, Z-forward relative to camera.
2. **Dense Cloud & Mesh**: Temporarily rotated during export (Z-up) for standard GIS interoperability.
3. **GLB Viewer Coordinates**: WebGL uses Y-up. The loader intrinsically maps GLB Z-up to WebGL Y-up.
4. **GPS/UTM Coordinates**: Valid strictly for Colorado (ABSOLUTE). MARS operates purely in local bounds.

## Restrictions
- Heatmap spatial indices must operate on the native scene_mesh.ply coordinate space before viewer-side orientation tricks.
- Z-values must never be blindly assumed as absolute elevation in RELATIVE datasets.
