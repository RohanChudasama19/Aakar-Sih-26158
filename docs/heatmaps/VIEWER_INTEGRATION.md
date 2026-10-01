# Viewer Integration

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
