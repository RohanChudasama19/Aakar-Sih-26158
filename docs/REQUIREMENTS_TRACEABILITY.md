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

| ID | Category | Description | Status | Evidence |
|---|---|---|---|---|
| Phase 0 | Baseline | Baseline and engineering hygiene (CI, Linting, Alembic, Logs) | COMPLETED | - |
| P1-01 | Input Gate | Stratified temporal frame sampling | **COMPLETED** | `app/pipeline/readiness.py` |
| P1-02 | Input Gate | Blur & exposure analysis | **COMPLETED** | `app/pipeline/readiness.py` |
| P1-03 | Input Gate | SIFT/ORB feature distribution | **COMPLETED** | `app/pipeline/readiness.py` |
| P1-04 | Input Gate | Geometric overlap & parallax estimation | **COMPLETED** | `app/pipeline/readiness.py` |
| P1-05 | Input Gate | Dataset connectivity graph | **COMPLETED** | `app/pipeline/readiness.py` |
| P1-06 | Input Gate | Mandatory telemetry validation | **COMPLETED** | `app/pipeline/readiness.py` |
| P1-07 | System | RECONSTRUCTION_BLOCKED DB state | **COMPLETED** | `app/db.py`, `app/pipeline/runner.py`, `app/worker.py` |
| P1-08 | Reports | JSON & TXT cv_quality_report generation | **COMPLETED** | `app/pipeline/runner.py` |
| Phase 2 | Calibration | Canonical classes, pipeline integration, undistortion, calibration script | **COMPLETED** | - |
| Phase 3 | SfM | Adaptive matching, verified pairs, global BA, backend abstraction | **COMPLETED** | `app/pipeline/sfm_backend.py` |
| Phase 4 | Fusion | Sensor fusion and metric georeferencing | Pending | - |
| Phase 5 | Quality | Geometry, surface and texture quality | Pending | - |
| Phase 6 | Semantics | Dynamic objects, semantics and confidence | Pending | - |
| Phase 7 | Outputs | Geospatial outputs and viewer | Pending | - |
| Phase 8 | Backend | Production backend and operations | Pending | - |
| Phase 9 | Benchmark | Benchmark and release evidence | Pending | - |
