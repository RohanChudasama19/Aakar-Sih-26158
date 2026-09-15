# AeroRecon Requirements Traceability Matrix

This document maps official system requirements to their implementation, tests, and evidence within the AeroRecon project.

## Core Requirements

| ID | Requirement | Implementation Status | Test Coverage | Evidence |
|---|---|---|---|---|
| REQ-01 | **3D mesh / point cloud** | Implemented (CPU baseline via Open3D Poisson; COLMAP planned) | `tests/test_surface.py`, `tests/test_pipeline.py` | Artifacts (OBJ, PLY, GLB) generated in pipeline. |
| REQ-02 | **<15 minutes processing for a 10-minute video** | Pending (Requires GPU COLMAP pipeline and benchmark) | Pending | Benchmark report will record times on target hardware. |
| REQ-03 | **<=1 m spatial accuracy** | Pending (Currently uses GPS fit residual; needs independent checkpoints) | Pending | Benchmark georeferencing suite with independent checkpoints. |
| REQ-04 | **Full visible-scene coverage** | Pending (Requires quantitative surface coverage metric, not just frame registration) | Pending | Coverage metric in `report.json`. |
| REQ-05 | **Output Formats** (OBJ, PLY, LAS, GeoTIFF, GLB/glTF, FBX) | Partially Implemented (Missing verified FBX and precise GeoTIFF DSM) | `tests/test_pipeline.py` (checks GLB, PLY, LAS, GeoTIFF presence) | Exported files verified by independent readers. |
| REQ-06 | **Web or desktop visualization** | Implemented (WebGL viewer) | Manual / E2E | WebUI with measurement tools (pending additions). |

## Architectural & Security Rules (Non-Negotiable)

| ID | Rule | Adherence Strategy | Verification |
|---|---|---|---|
| SEC-01 | No arbitrary code execution from untrusted models (e.g. `.pt`, `.pkl`) | Custom PT loading is gated by `ALLOW_TRUSTED_PT`. | API request validation, CI security checks. |
| ARC-01 | No fake data, hardcoded success, or mock geometry | Real measurements only. Learned/inferred features kept separate. | Code review, Benchmark validation. |
| ARC-02 | Typed, maintainable modules over one-liners | MyPy/Pyright typing enforcement in CI. | Pre-commit hooks, CI pipelines. |
| ARC-03 | Emit evidence, timings, warnings, and metrics at every stage | Pipeline stages write to `report.json` and `events.jsonl`. | Pipeline unit tests. |

## Feature Phases Tracking

| Phase | Description | Status |
|---|---|---|
| Phase 0 | Baseline and engineering hygiene (CI, Linting, Alembic, Logs) | In Progress |
| Phase 1 | Ingest and reconstruction-readiness gate | Pending |
| Phase 2 | Camera model and calibration | Pending |
| Phase 3 | Production SfM + GPU dense reconstruction | Pending |
| Phase 4 | Sensor fusion and metric georeferencing | Pending |
| Phase 5 | Geometry, surface and texture quality | Pending |
| Phase 6 | Dynamic objects, semantics and confidence | Pending |
| Phase 7 | Geospatial outputs and viewer | Pending |
| Phase 8 | Production backend and operations | Pending |
| Phase 9 | Benchmark and release evidence | Pending |
