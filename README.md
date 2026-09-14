# AeroRecon

**A runnable reference application for SIH 26158: single-pass video → camera poses → textured surface → spatial exports.**

This repository implements a real, reduced-fidelity end-to-end geometric reconstruction workflow and a browser interface. It is **not a completed production-grade implementation of the entire aspirational brief**. The CPU workflow is exercised on the supplied synthetic clip and the real Zurich aerial subset. See docs/SURFACE_FIX.md for the real-footage result and remaining limitations. CUDA/COLMAP deployment is supplied but must be tested on your GPU. The <15-minute / ≤1 m targets are **not demonstrated**. Read the requirement matrix below before evaluating it.

The download also includes an offline Git bundle. You can clone it with `git clone aerorecon-repository.bundle AeroRecon`, then open the cloned folder. Extracting and running the source folder works equally well.

## Start here — Windows with Docker Desktop

1. Install Docker Desktop with Linux containers / WSL2 and allocate at least 8 GB RAM (16 GB recommended).
2. Extract the ZIP and open a terminal inside the `aerorecon` folder.
3. Run:

```powershell
docker compose up --build
```

4. Open **http://localhost:8000**. Wait for “1 reconstruction worker(s) online.” The first container build downloads dependencies and can take several minutes; that is separate from processing time.
5. Click **New mission → Use bundled sample files → Start reconstruction**. Leave the CPU engine selected.
6. Follow stages A–F. Open the result, rotate/zoom, use distance or planar area tools, and download the complete result bundle.

The default Compose setup is **local development only** and binds exposed ports to 127.0.0.1. PostgreSQL, Redis and MinIO persist in Docker volumes. `docker compose down` stops services without deleting data. Do not use `down -v` unless you intend to delete it.

If you set `API_TOKEN` in `.env`, enter the same token through **API access settings** in the sidebar. Auth uses a shared deployment token, not multiuser accounts. Sample download links in the quick-start dialog require an auth-aware client when a token is enabled; the sample-loading button works with the token.

## Run without Docker — CPU

Python 3.11 recommended (3.10–3.12 supported). Node is **not required to start**: the downloadable archive includes local Three.js browser dependencies.

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Linux/macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://localhost:8000. Local mode uses SQLite, filesystem artifacts and one background CPU thread; the Docker deployment uses Postgres + RQ/Redis + MinIO. Keep the local server running until jobs finish. On restart, interrupted local jobs are marked failed.

For FBX locally, install **Blender** and put `blender` on PATH. Docker images include Blender. Without it, other formats are exported and the report marks FBX unavailable rather than creating a mislabeled file.

## Worked sample

All three required inputs are already in `samples/`:

| File | Content |
|---|---|
| `sample.mp4` | 6 seconds, 640×480, 10 FPS, 60 frames; a rendered textured ground and three structures |
| `gps.csv` | Exact requested columns, 60 UTC-timestamped synthetic GPS samples |
| `flight.json` | Exact requested flight metadata keys, with known synthetic camera intrinsics |
| `ground_truth.json` | Synthetic camera poses used to render the clip; not real surveyed validation |
| `rtk-example.csv` | Optional zero corrections, demonstrating the correction schema |
| `barometer-example.csv` | Optional altitude track in the same datum |

A smoothly curved **single pass** is used so the absolute orientation can be constrained; a perfectly collinear GPS track cannot by itself resolve rotation about its flight axis. The renderer is deterministic and included as `scripts/generate_sample.py`. No downloaded drone footage is needed.

Run the pipeline directly:

```bash
python scripts/smoke.py
```

Results go to `data/cli-smoke/work/outputs/` and `data/cli-smoke/work/artifacts.zip`. These are actual image-derived reconstructions, not the synthetic scene's original geometry. The pipeline does not read `ground_truth.json`.

An official YOLO checkpoint **is not included**. To obtain the optional small default checkpoint:

```bash
python -m pip install -r requirements-models.txt
python scripts/download_models.py
```

Then set `SEGMENTATION_MODEL` to the absolute `weights/yolov8s-seg.pt` path for both the API/worker runtime. For Docker, mount weights into the worker and set the path in **both API and worker** environments. The weights and optional neural path were not validated in the CPU smoke test. Ultralytics model/software licensing must be reviewed before distribution or a hosted service.

## GPU / dense mode

Assumed target hardware: **NVIDIA RTX 4090-class GPU with 24 GB VRAM**, 32 GB system RAM and SSD storage. A compatible host driver, Docker GPU support and NVIDIA Container Toolkit are required for the CUDA mode. GPU is required for the provided COLMAP PatchMatch configuration; CPU is an explicitly reduced-fidelity alternative for testing.

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

Select **CUDA · COLMAP dense stereo** in the form. The GPU Dockerfile builds COLMAP 3.9.1 with CUDA 12.2.2 and pinned CLI conventions. Initial compilation is substantial and is **not** included in reconstruction runtime. This container was not built/run in the delivery environment, which had neither Docker nor a CUDA GPU. Driver/toolchain compatibility remains a deployment validation step.

GPU mode uses incremental COLMAP SfM + geometric-consistency PatchMatch MVS. It intentionally substitutes measured multiview stereo for the requested Gaussian-Splatting / monocular-hole-filling hybrid. This improves traceability but does **not** solve occluded geometry or establish the requested speed budget. Meshing/texturing remain the reduced-fidelity implementation described below.

## Implemented pipeline

| Stage | Implementation | Limits |
|---|---|---|
| A · ingest | OpenCV video decoder with FFmpeg backend, motion-driven optical-flow selection, blur rejection, CLAHE, optional YOLO dynamic-object masks | No learned deblurring. Default weights not bundled. Frame budget may truncate long inputs and is reported. |
| B · poses | SIFT + ratio test + essential-matrix RANSAC, incremental PnP, positive-depth/parallax-checked triangulation; or COLMAP with bundle adjustment | CPU path refines each PnP pose but has no global bundle adjustment. Intrinsics must be supplied, zero lens distortion assumed. |
| B · GPS | Robust Sim(3) alignment to interpolated UTM camera positions; optional additive RTK/PPK corrections and barometer altitude | No ESKF/IMU fusion or joint pose graph. Nearly collinear trajectories yield relative-only output. |
| C · dense | Calibrated rectification, SGBM with left/right consistency plus bidirectional LK tracking/triangulation, mask filtering, sparse-envelope pruning, voxel deduplication; or COLMAP MVS | CPU supports positive horizontal disparity pairs. Unsupported pairs are skipped; sparse evidence remains. No trained 3DGS. |
| C · optional depth | ONNX Z-depth model, sparse-depth median scale fit, rejection of inconsistent views | Inferred points saved separately, not fused into measured mesh. Model contract must match exactly. |
| D · surface | 3D screened Poisson with camera-oriented normals, outlier removal, support trimming; per-face image atlas | Preserves vertical surfaces; interpolated geometry may be wrong or incomplete. No guaranteed watertightness, multiband blending or full visibility test. |
| E · export | Textured OBJ+MTL+PNG, PLY, GLB, glTF+dependencies, LAS, observed DSM/RGB ortho GeoTIFF; Blender FBX adapter | LAS/GeoTIFF require resolved metric frame. GeoTIFF DSM is not a classified bare-earth DEM. FBX needs Blender. |
| F · report | Candidate point/face labels, class fractions/areas, stage timings, registration and alignment metrics | Semantic labels are unvalidated color/height heuristics, not a trained UAVid model. No calibrated confidence probability. |

**No explicit occluded-surface completion is performed.** Meshing interpolates between observed points and can bridge small unsupported regions. Gaussian splatting and monocular depth do not provide independent evidence for hidden surfaces. The original brief's claim that they resolve occluded-surface accuracy is not a valid guarantee.

## Requirement coverage / remaining work

| Brief item | Delivered status |
|---|---|
| Required video/GPS/metadata upload | Implemented, with schema and numeric checks |
| IMU, barometer, intrinsics, RTK optional fields | All fields exist; barometer/intrinsics/RTK applied; IMU archived and disclosed as unfused |
| Custom segmentation/depth/pose weights | Trusted YOLO + ONNX depth contracts implemented; pose checkpoint overrides unsupported |
| Default deblur + segmentation + aerial semantic networks | Not delivered as defaults; blur rejection and heuristic semantics are working substitutes; YOLO optional |
| SfM, dense geometry, textured surface | Implemented CPU; additional unvalidated CUDA adapter |
| ESKF / pose graph sensor fusion | Not implemented; robust trajectory similarity alignment substitute |
| Fast trained 3D Gaussian Splatting + unified monocular field | Not implemented; calibrated stereo substitute; optional inferred depth saved separately |
| Watertight mesh, complete facades, occlusion completion | Not guaranteed; 3D interpolated surface trimmed to nearby observations |
| All output format paths | Implemented; FBX conditional on Blender, geospatial formats conditional on resolved coordinates |
| Bare-earth DEM | Not implemented; DSM supplied and named correctly |
| Live stages, viewer, distance/area, downloads | Implemented |
| Queue, Postgres, Redis, object storage, Compose | Implemented integration; Compose/GPU infrastructure not runtime-tested here |
| Multiuser production service | Not delivered; shared token and localhost development deployment |
| <15 min / 10 min video, ≤1 m, full visible scene | Unverified targets; reports keep pass status null without supporting evaluation |

## Accuracy, coordinate frames and confidence

- Visual SfM starts at arbitrary scale. A robust similarity transform aligns camera centres to the GPS trajectory.
- Mesh vertices / PLY are in a local frame. When alignment is resolved, this is **X east, Y north, Z up**, in metres, relative to the UTM origin in `georeference.json`.
- LAS/GeoTIFF use **absolute UTM** coordinates with the EPSG CRS embedded. Latitude zone boundaries, very large regions and polar missions require a more suitable project CRS than the automatic UTM choice.
- Altitude uses the source datum as given. There is no ellipsoid-to-geoid conversion. Never mix ellipsoidal and orthometric heights without conversion.
- GPS RMSE is measured **against the track used to fit the transform**. A small residual is not proof of metre-level absolute accuracy. Systematic GPS bias, calibration error and unobserved surfaces can still dominate.
- Camera registration fraction measures which selected images contribute poses; it is not a surface-completeness percentage. Surface coverage is left null.
- No calibrated confidence heatmap is claimed. Reports expose evidence indicators and explicit limitations.
- A survey-quality evaluation needs independently measured checkpoints withheld from alignment, along with RMSE/percentile errors and a reference surface coverage test.

## Storage, jobs and operation

- Video uploads are streamed from the multipart spool to job storage; upload progress is shown separately. Upload time scales with file size, disk and network bandwidth. FastAPI must still receive the file before starting processing; there is no multipart resumable/direct-S3 protocol in this version.
- API verifies a worker is registered before queueing. RQ job timeout is three hours, and queue failures / stale application heartbeats are surfaced. The worker emits a heartbeat every ten seconds during long stages. COLMAP subprocess logs are in `work/colmap.log`.
- Input and output files are mirrored to MinIO upon successful completion. Shared local volume remains the serving and processing store. This is a single-host reference deployment, **not** distributed object-store-native workers.
- RQ allows additional worker processes; GPU memory needs admission control before concurrency is increased. Do not run multiple dense jobs on one GPU without a resource budget.
- A reverse proxy with TLS, OIDC/session auth, per-user job ownership, quotas, rate limits, malware/model isolation, database migrations, backup/retention, crash-recovery and validated model licences is required before exposing this service publicly.
- Shared API token protects all `/api/` endpoints when enabled. It is intentionally not passed in URLs or persisted across browser sessions. Any token holder can see all jobs.

Troubleshooting:

```bash
docker compose ps
docker compose logs --tail 100 worker api
```

If “no worker online” appears, fix the worker container before retrying. If SfM reports insufficient parallax, use a translated camera path with persistent textured overlap. Increasing the frame budget does not make pure rotation reconstructable. Choose a smaller video for the first real-world test.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests exercise known-transform recovery, calibrated triangulation, rejected inputs, checkpoint loading restrictions, all six real CPU stages, and re-reading GLB/PLY/LAS/GeoTIFF artifacts. The end-to-end test uses actual decoded synthetic video frames; no fixture bypass injects the geometry. See `docs/VALIDATION.md` for the delivery-run evidence and untested paths.

## Browser dependencies

The archive includes Three.js under its MIT licence. To regenerate those assets after a source-only checkout:

```bash
npm ci
npm run vendor
```

Fonts are optional remote Google Fonts with system fallbacks. All functional JavaScript and the viewer are served locally. No map tiles or external inference service is required.

## Repository tree

```
aerorecon/
  app/
    main.py                  # Uploads, jobs, SSE, downloads, static web app
    config.py db.py storage.py schemas.py worker.py
    pipeline/
      preprocess.py sfm.py georef.py dense.py colmap.py
      depth.py surface.py mesh.py exports.py semantic.py runner.py
  web/
    index.html style.css app.js viewer.js vendor/
  scripts/
    generate_sample.py smoke.py export_fbx.py download_models.py
    start-local.ps1 start-local.sh vendor.mjs
  samples/
    sample.mp4 gps.csv flight.json ground_truth.json
    rtk-example.csv barometer-example.csv
  tests/
    conftest.py test_geometry.py test_inputs_api.py test_pipeline.py
  docs/
    INPUT_FORMATS.md VALIDATION.md ORIGINAL_REQUIREMENTS.md
  Dockerfile Dockerfile.gpu
  docker-compose.yml docker-compose.gpu.yml
  requirements.txt requirements-dev.txt requirements-models.txt
  pyproject.toml package.json package-lock.json .env.example
```

## Primary technical references

- [COLMAP command-line interface](https://colmap.github.io/cli.html) — feature extraction, incremental mapping and dense stereo commands.
- [RQ documentation](https://python-rq.org/docs/) — asynchronous jobs and worker operation.
- [trimesh texture visuals](https://trimesh.org/trimesh.visual.texture.html) — UV/material storage and mesh exports.
- [Ultralytics segmentation documentation](https://docs.ultralytics.com/tasks/segment/) — optional YOLO instance segmentation contract.

The supplied build prompt is preserved in `docs/ORIGINAL_REQUIREMENTS.md`. This README deliberately distinguishes its desired system from the implemented and tested subset.
