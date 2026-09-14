# Build Prompt for GPT-6 Astra — Single-Pass Drone Video → 3D Model System (SIH PS 26158)

Copy everything below this line into GPT-6 Astra as a single prompt.

---

You are GPT-6 Astra, working with full coding, computer-use, and agentic capability. Your task is to **design, build, and deliver a complete, runnable, production-quality web application** for the problem below. Do not describe or summarize a solution — actually build it: write every file in full (no `// TODO` placeholders for core logic), create the full repository structure, and leave me with something I can `git clone` and run.

## 1. Problem context (verbatim from the official problem statement)

**Title:** Single-Pass Drone Video to Accurate 3D Model Generation System
**Organisation:** National Technical Research Organisation | **Category:** Software | **Theme:** Drone/Robotics

**Background:** Accurate 3D models of buildings, infrastructure, terrain, and objects normally require multiple drone passes, heavy image overlap, specialized flight planning, and long post-processing. In disaster response, surveillance, infrastructure inspection, military reconnaissance, and rapid mapping there is often only one opportunity to capture the area. A system that produces an accurate, textured 3D model from a **single drone pass video** would cut mission time, operator effort, data needs, and processing complexity while enabling near real-time situational awareness.

**Must reconstruct:** (i) 3D terrain & structures (ii) building facades & rooftops (iii) roads & infrastructure (iv) vegetation & obstacles (v) textured 3D meshes or point clouds.

**Key challenges to explicitly address in your design:** limited viewing angles (single flight path), motion blur / compression artifacts, variable illumination and shadows, dynamic objects (vehicles, humans, animals), GPS inaccuracy and sensor noise, real-time/near-real-time processing, reconstruction of occluded surfaces, metric accuracy without extensive Ground Control Points.

**Input data — Mandatory:** drone video (1080p/4K), GPS coordinates, flight metadata.
**Input data — Optional:** IMU data, barometric altitude, camera intrinsic parameters, RTK/PPK corrections.

**Desired output targets:**

| Parameter | Target |
|---|---|
| Reconstruction type | 3D mesh / point cloud |
| Processing time | < 15 min for a 10-min video |
| Spatial accuracy | ≤ 1 m |
| Coverage | Entire visible scene |
| Output formats | OBJ, PLY, LAS, GeoTIFF, .glb/.gltf, .fbx |
| Visualization | Web-based or desktop viewer |

**Evaluation weighting:** Reconstruction accuracy 30% · Model completeness 20% · Processing speed 20% · Innovation 15% · Scalability 10% · UI 5%.

## 2. What to build

A full-stack web application (working name: **AeroRecon** — rename if you have a better one) that:

1. Accepts one drone video plus mandatory GPS + flight metadata, and optional IMU / barometric altitude / camera intrinsics / RTK-PPK corrections, and optional **custom model checkpoints** (advanced users can plug in their own fine-tuned segmentation, depth, or pose-estimation weights instead of the defaults).
2. Runs an automated reconstruction pipeline end-to-end with live progress reporting.
3. Produces a georeferenced, textured 3D model, viewable and measurable in-browser, downloadable in all required formats.

## 3. Assumed technical architecture

Single-pass video gives strong **along-track** frame overlap (consecutive frames are 90%+ similar) but a narrow **cross-track** stereo baseline — the opposite of classic multi-pass photogrammetry. Design around that asymmetry. Use this pipeline unless you have a clearly better one — if you deviate, say why in the README.

**Stage A — Ingest & preprocess**
- Decode video (ffmpeg), extract frames at an adaptive rate driven by estimated motion/parallax (not a fixed FPS) so overlap stays sufficient without wasting compute on near-duplicate frames.
- Deblur motion-blurred frames (a lightweight deblurring network, e.g. a distilled DeblurGAN-v2-class model) and discard frames below a sharpness threshold (variance-of-Laplacian) rather than feeding them into SfM.
- Normalize exposure/illumination across frames (histogram/CLAHE-based) so shadows don't fragment feature matching.
- Run instance segmentation (default: YOLOv8-seg small model, swappable via the optional checkpoint upload) to mask out dynamic objects — vehicles, humans, animals — before they pollute the static reconstruction. Log what was masked for the completeness metric.

**Stage B — Pose estimation (robust to GPS noise + narrow baseline)**
- Run incremental Structure-from-Motion (COLMAP or an equivalent open pipeline) on the masked frames for visual pose + sparse point cloud.
- Loosely fuse visual poses with GPS (mandatory) and IMU (if supplied) via an extrinsic Kalman filter / pose-graph optimization — this is what keeps pose estimates stable when SfM alone is weak due to the narrow baseline, and is what lets you meet ≤1m accuracy without extensive GCPs.
- If RTK/PPK corrections are supplied, use them to directly correct the GPS trajectory before fusion — call this out in the UI as a large accuracy boost when present.

**Stage C — Dense / neural reconstruction (this is the core "single-pass" innovation — weight it heavily, it's 30%+15% of the score)**
- Use the SfM sparse point cloud + fused poses to initialize a fast 3D Gaussian Splatting reconstruction (an InstantSplat-style few-minute initialization, not a from-scratch multi-hour train) — this is what lets you hit occluded-surface and single-view coverage gaps that pure multi-view stereo can't fill, while staying inside the 15-minute budget.
- In parallel, run a monocular metric-depth model (e.g. a Depth Anything V2 / Metric3D-class model) on frames with poor multi-view support, scale-aligned to the sparse SfM point cloud, to patch coverage holes from the single flight path.
- Fuse the Gaussian splat field and the monocular-depth-filled regions into one consistent point/opacity field before meshing.

**Stage D — Mesh extraction & texturing**
- Extract a watertight mesh via Poisson surface reconstruction or TSDF fusion over the fused field.
- Texture by re-projecting original (unmasked-background) video frames onto the mesh, picking the best-angle frame per face and multi-band blending seams so illumination changes don't create visible patchwork.

**Stage E — Georeferencing & export**
- Anchor the whole model to real-world coordinates using the GPS track and barometric/GPS altitude (RTK/PPK if present).
- Export: OBJ, PLY, LAS (point cloud), GeoTIFF (ortho + DEM), glTF/GLB, FBX. Use Open3D / PDAL / trimesh / Assimp rather than hand-rolling format writers.

**Stage F — Semantic layer (this is what earns "innovation" and "completeness" points)**
- Run a second, coarser semantic segmentation pass (terrain / building / road / vegetation classes — e.g. a model fine-tuned on an aerial dataset such as UAVid) and attach per-vertex/per-point class labels so the output supports the "damage assessment / urban planning / infrastructure inspection" use cases the problem statement lists, not just raw geometry.
- Emit a short auto-generated scene report (class-wise area/coverage %, detected dynamic-object count, estimated reconstruction confidence) alongside the model.

## 4. Frontend requirements

- Job submission form with fields exactly matching Section 1's input list: **Drone video** (required), **GPS coordinates / telemetry CSV** (required), **Flight metadata JSON** (required), and an **Advanced options** section with IMU data, barometric altitude, camera intrinsics, RTK/PPK corrections, and custom model checkpoints — all optional.
- Live pipeline progress (WebSocket/SSE) through the named stages (A–F above), not a single spinner.
- In-browser 3D viewer (Three.js, or Potree specifically for the point-cloud/LAS output, plus a lightweight Cesium/MapLibre layer if you want the GeoTIFF ortho georeferenced on a map) supporting rotate/pan/zoom and basic **distance/area measurement tools** — the problem statement explicitly asks for "visualization, measurement, and analysis."
- Per-job results page: download links for every export format, the scene report from Stage F, and the processing-time/accuracy self-reported metrics.

## 5. Backend / infrastructure

- Python backend (FastAPI) with an async job queue (Celery + Redis, or RQ) so uploads return immediately and processing happens on GPU worker containers.
- Object storage for uploaded videos and output artifacts (S3-compatible / MinIO is fine for local dev).
- Postgres for job/user/metadata state.
- Docker Compose for local dev; include a `docker-compose.yml` that brings up API, worker, Redis, Postgres, and MinIO with one command.
- GPU (CUDA) required for Stages B–D; note this clearly in the README's system requirements.

## 6. Non-functional targets — mirror these exactly, and self-report against them in the scene report

- Processing time < 15 min for a 10-minute input video (on a single modern GPU — state which one you assumed, e.g. RTX 4090-class).
- Spatial accuracy ≤ 1 m (report your estimated error using GPS-track reprojection residuals if no ground truth is available).
- Full visible-scene coverage — track and report % of frames successfully registered.

## 7. Deliverables — what "done" means

- Full repository, every file written out completely, correct relative imports, no missing modules.
- A repo tree in the README.
- `requirements.txt`/`pyproject.toml`, Dockerfiles, `docker-compose.yml`.
- README with: setup instructions, how to run, and a **worked example using this exact sample data** so I can smoke-test immediately:
  - Video: a short MP4 (any short aerial or generic clip works for a pipeline smoke test)
  - GPS telemetry CSV with columns: `timestamp_utc, frame, latitude, longitude, altitude_m, compass_heading_deg, gimbal_pitch_deg, gimbal_yaw_deg, speed_mps, satellites`
  - Flight metadata JSON with fields: `mission_name, drone_model, camera_sensor, video_file, video_resolution, video_fps, video_duration_sec, home_point{latitude,longitude,altitude_m}, start_time_utc, end_time_utc, camera_intrinsics{focal_length_mm,sensor_width_mm,sensor_height_mm,image_width_px,image_height_px}`
  - An example optional checkpoint: a small YOLOv8-seg `.pt` file, to demonstrate the custom-checkpoint override path
- A short automated test (even a smoke test that runs the pipeline on a tiny clip and asserts each stage produces non-empty output) so I know the thing actually runs, not just compiles.
- If any single component is genuinely infeasible to fully implement in one pass (e.g., training a full neural model from scratch), implement a **working, reduced-fidelity version** that still produces a valid, correct end-to-end output (smaller model, fewer splat iterations, coarser mesh) and clearly comment where a production deployment would swap in the heavier version.

## 8. Evaluation alignment (keep this visible while you build — don't let one criterion crowd out the others)

Reconstruction accuracy 30% (Stage B fusion + RTK/PPK path) · Completeness 20% (Stage C occlusion-filling + Stage F semantic coverage) · Speed 20% (adaptive frame sampling + fast Gaussian-splat init, not full multi-hour NeRF training) · Innovation 15% (the hybrid SfM+splat+monocular-depth fusion approach, and the semantic layer) · Scalability 10% (job queue + containerized workers) · UI 5% (the web viewer + measurement tools).

Build it now — full code, full repo, working end-to-end example included.
