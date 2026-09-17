# AeroRecon - SIH 26158 Final Release

## What AeroRecon Does
AeroRecon is a fully automated 3D reconstruction pipeline designed to process UAV video and GPS telemetry into metric 3D models and orthomosaics. It implements robust readiness validation, Structure-from-Motion (SfM), dense Multi-View Stereo (MVS), surface meshing, texturing, and heuristic semantic classification. 

## Requirements
* Windows 10/11 or Linux
* Python 3.10+
* NVIDIA GPU (CUDA 11.8+) with at least 8 GB VRAM recommended (tested on 4 GB RTX 3050)
* Redis (for background task queuing)
* **COLMAP 4.1+** installed and available in system PATH
* **Blender** (optional, required for FBX export)

## Installation & Quick Start
1. Clone this repository.
2. Run pip install -r requirements.txt.
3. Ensure a Redis server is running locally on port 6379, or configure REDIS_URL.
4. Start the background worker: python -m app.worker
5. Start the web API: uvicorn app.main:app --port 8000
6. Navigate to http://localhost:8000 to access the AeroRecon Mission UX.

## Required Inputs
* Drone video (MP4, MOV, MKV) with steady lateral camera motion.
* GPS telemetry (CSV) aligned to the video duration.
* Flight metadata (JSON) defining drone/camera properties.

## Optional Inputs
* Barometric altitude CSV
* Camera intrinsics JSON
* RTK / PPK corrections CSV

## Pipeline Overview
* **Ingest & Prepare:** Extracts frames, validates GPS synchronization, and filters blurry inputs (Readiness Gate).
* **Camera Poses:** Recovers sparse geometry and poses using COLMAP SfM.
* **Georeference:** Aligns the relative trajectory to the GPS track using a robust Sim(3) transform.
* **Dense Geometry:** Generates depth maps and fuses them into a dense point cloud (PatchMatchStereo).
* **Mesh & Texture:** Reconstructs a Poisson surface and textures it using ray-casting occlusion (Single-best-view).
* **Semantics:** Classifies the model structurally (Ground, Building, Vegetation, etc.) via heuristic fallbacks (AI segmentation unavailable).

## Viewer and Outputs
The browser UI streams live task progress via SSE. Upon completion, users can explore the mission in a 6-mode 3D viewer (Textured, Mesh, Dense, Sparse, Semantic, Confidence) or 2D Map mode.
Measurements for distances, area, and slope are supported.
All final deliverables are zipped, generating standard formats: **PLY, OBJ, LAS, GeoTIFF, GLB, GLTF, FBX**.

## Limitations
* **Independent $\leq1$ m accuracy not yet validated:** Metric alignment uses GPS for scaling/translation, but no independent survey checkpoints are currently available for blind validation.
* **Official 10-minute runtime target not benchmarked:** Target of <15 min for a 10 min dataset is unachievable on tested low-end hardware (estimated 4 hours on RTX 3050 laptop).
* **Large-mission scalability not verified:** Validated extensively on 25-frame datasets.
* **Semantic backend currently heuristic:** No bundled AI segmentation model due to licensing and size constraints.
* **Multiband texture seam blending not implemented:** Hard pixel assignment leads to visible UV seams.
* **Single-Tenant Assumption:** No multi-tenant authentication or robust path isolation is enforced.

## Demo Instructions
1. In the Web UI, click "Use bundled sample files".
2. It will stage a synthetic flight (6-seconds).
3. Select 'CPU' and click Start for a rapid end-to-end smoke test.
