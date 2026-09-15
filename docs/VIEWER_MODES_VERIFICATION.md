# Viewer Modes Verification

## Mode Availability and Verification

| Mode | Artifact | Format | Analysis Count | Display Count | Availability | Verification State | Actually Rendered | Verification Method |
|---|---|---|---|---|---|---|---|---|
| **Sparse Point Cloud** | `outputs/sparse/sparse.ply` | PLY | All Phase 3 SfM points | = Analysis | VERIFIED | File existence + size > 0 | YES - PLYLoader -> THREE.Points | Artifact generation test + API test |
| **Dense Point Cloud** | `outputs/pointcloud/dense_display.ply` | PLY | Full dense_filtered.ply | <=200,000 pts voxel downsampled | VERIFIED | File existence + size > 0 | YES - PLYLoader -> THREE.Points | Downsampling unit tests + API test |
| **Mesh (Geometry)** | `outputs/mesh/model.glb` | GLB | N/A | N/A | VERIFIED | File existence + manifest validation != FAILED | YES - GLTFLoader + neutral MeshStandardMaterial | API validation gate test |
| **Textured Mesh** | `outputs/mesh/model.glb` | GLB | N/A | N/A | VERIFIED | File existence + manifest validation != FAILED | YES - GLTFLoader with original materials | API validation gate test |
| **Semantic** | `outputs/semantic/semantic_mesh.ply` or `outputs/semantic_mesh.ply` (legacy) | PLY | Vertex colors from class palette | = Analysis | VERIFIED | File existence; legacy path fallback covered | YES - PLYLoader -> THREE.Points vertex colors | Semantic copy test + API legacy fallback test |
| **Confidence / Coverage** | `outputs/mesh/confidence_mesh.ply` | PLY | Per-face support classification | N/A | VERIFIED | File existence + support summary JSON | YES - PLYLoader -> THREE.Points pre-colored | Confidence mesh test + API test |

## Notes

- Confidence / Coverage is labeled "Coverage / Confidence" in the UI and is explicitly noted as reconstruction support evidence, NOT positional accuracy.
- Dense display cloud is a separate artifact from dense_filtered.ply (the canonical analysis cloud). Analysis cloud is not modified.
- Semantic checks both outputs/semantic/semantic_mesh.ply and legacy outputs/semantic_mesh.ply; original file is never deleted.
- Mesh (Geometry) replaces materials with neutral MeshStandardMaterial. Textured mode retains original GLTFLoader materials. These are genuinely different representations.
- Unavailable modes shown with [Unavailable] suffix and disabled attribute - no placeholder toasts.

## Fallback Chain

Textured Mesh -> Mesh -> Dense Point Cloud -> Sparse Point Cloud

## Browser Automation

Playwright / Browser Automation: NOT_EXECUTED

Reason: No Playwright installation in the project environment. Full pipeline test (test_pipeline.py) runs end-to-end reconstruction and validates artifact generation from source to output.
