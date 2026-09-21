# Dynamic Object Masking

AeroRecon leverages its multi-view awareness combined with AI semantic segmentation to reliably erase moving objects (cars, pedestrians) from 3D reconstruction.

## The Problem
Photogrammetry fundamentally assumes static scenes. When objects move, they cause:
- Conflicting feature matches
- "Ghosting" artifacts in textured meshes
- Spurious geometry in depth maps

## Dynamic Masking Pipeline
1. **2D Semantics:** The ONNX model processes individual frames. `Human` and `MovingCar` predictions are classified as `SEMANTIC_DYNAMIC_CANDIDATE`.
2. **Temporal Confirmation:** Features that fall inside a dynamic candidate mask are tracked across adjacent views. If the epipolar geometry indicates movement, or if the confidence is high across multiple distinct views, the mask is promoted to `TEMPORALLY_CONFIRMED_DYNAMIC`.
3. **Exclusion:**
   - Features within confirmed dynamic masks are stripped from the Sparse SfM matching pool.
   - Depth map generation ignores pixels belonging to these masks.
   - Mesh texturing ignores these regions, relying on background views to fill in the occlusion.

## Modes
- **Conservative (Default):** Requires strong temporal confirmation. Preserves static cars (OBSTACLE).
- **Aggressive:** Masks all dynamic candidates unconditionally. 
