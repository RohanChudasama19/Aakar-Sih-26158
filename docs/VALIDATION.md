# Delivery validation — 2026-09-13

## Executed successfully

- Python 3.12 on Linux, CPU; pinned requirements installed.
- `python -m pytest -q` from the repository root: **10 passed**, 2 upstream deprecation warnings, 14.88 seconds.
- The real CPU pipeline decoded the included 6-second MP4, selected and registered **16/16 cameras**, and completed stages A–F.
- Measured pipeline time in the packaged test report: **12.835 seconds**. The separate browser run took about 10.9 seconds. These small synthetic timings are not a 10-minute/GPU benchmark.
- Mesh: **9800 pre-atlas vertices**, **9987 triangles**. Geometry is intentionally reduced fidelity and visibly incomplete; see viewer screenshot.
- Bidirectional tracked-stereo samples accepted: **23998**; SGBM samples accepted: **659**, before combined deduplication/downsampling.
- GLB, PLY, LAS and GeoTIFF were read back with independent file readers from their respective libraries; CRS, counts and non-empty geometry/data were checked.
- LAS candidate classifications and semantic sidecar are produced. Their semantic accuracy is not validated.
- Real multipart submission returned HTTP 202. The local worker ran the job, the live SSE endpoint reported progress, and the result download returned HTTP 200 with a valid ZIP.
- Browser workflow: opened the UI, loaded the actual bundled input files into file controls, submitted the mission, awaited completion, loaded the generated GLB into a WebGL canvas, toggled measurement mode/wireframe, and returned to the mission list.
- Browser page errors: **0**. At 390 px viewport width: **no horizontal document overflow**.
- JavaScript syntax and Python compilation checked. Both Compose YAML files parse and include the expected service configuration.

The test suite checks similarity-transform recovery, positive-depth triangulation, intrinsics scaling, collinear-track ambiguity, required fields, malformed GPS, unavailable jobs/engines, disabled untrusted PT uploads, shared API authentication, and full CPU reconstruction/export roundtrips.

## Evidence included

- `samples/sample-result.zip`: outputs from the final end-to-end CPU test.
- `docs/sample-report.json`: timings, registration, alignment, export status and all runtime limitations.
- `docs/screenshots/dashboard.png`: empty desktop mission workspace.
- `docs/screenshots/dashboard-complete.png`: completed mission workspace.
- `docs/screenshots/upload.png`: sample files selected in the submission form.
- `docs/screenshots/viewer.png`: actual reconstructed sample in the browser.
- `docs/screenshots/mobile.png`: responsive mission workspace.

## Not validated here

- Docker Compose startup or RQ/Redis/Postgres/MinIO integration in containers. No Docker daemon was available.
- CUDA build, COLMAP feature extraction / mapping / PatchMatch on an NVIDIA GPU.
- Blender FBX export. Blender was unavailable; FBX is marked unavailable in the included sample report. It is installed by the provided Dockerfiles.
- Optional YOLO or ONNX depth model inference, checkpoint download, and model licensing for a deployment.
- Numerical browser measurements against an independently surveyed reference object.
- Real aerial footage, calibrated distortion, GPS multipath, datum conversion, metric accuracy, scene completeness, or a ten-minute performance target.
- Trained Gaussian splatting, learned deblurring, learned aerial semantic segmentation, IMU ESKF, pose-checkpoint swaps and watertight meshing: these are not implemented and are listed in the README requirement matrix.

The screenshots show a **coarse, incomplete reconstructed surface**, not a photorealistic or survey-grade model. The available CPU result demonstrates executable plumbing and geometric reconstruction. Higher-quality modelling remains engineering/evaluation work, not a validated claim of this delivery.
