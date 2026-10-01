# Phase 0 Baseline Report

This document records the baseline state of the AAKAR project before Phase 0 hygiene changes were applied.

## 1. Test Suite Verification
**Command Executed:** `python -m pytest tests/`
**Result:** 11 passed, 2 warnings in ~28.7s.
**Coverage:** (Not fully measured yet, but unit tests exist for pipeline, surface, geometry, and api).

**Status:** Verified working in the current environment.

## 2. CPU Sample Workflow
**Command Executed:** `python -m scripts.smoke`
**Result:** The CLI smoke test ran successfully through stages A (Ingest) to F (Semantic layer & report). It completed and produced the final artifact `artifacts.zip` containing `model.glb`, `model.obj`, `cloud.ply`, `report.json`, and `semantic_labels.npz`.

**Status:** Verified working.

## 3. Supported Python Versions
**Documented target:** Python 3.10 – 3.12.
**Current execution environment:** Python 3.11.9.

**Status:** Verified running on Python 3.11.9; compatibility with 3.10 and 3.12 is intended and will be codified in CI.

## 4. API Behavior
The following REST API endpoints currently exist and function without a stable JSON error structure (currently raises standard FastAPI/HTTPExceptions):
* `GET /api/health` - System capability and queue state.
* `POST /api/jobs` - Ingests multipart files (video, telemetry, models) and enqueues reconstruction.
* `GET /api/jobs` - Lists up to 100 recent jobs.
* `GET /api/jobs/{jid}` - Retrieves job status and progress.
* `GET /api/jobs/{jid}/events` - Server-Sent Events (SSE) stream for live reconstruction progress.
* `GET /api/jobs/{jid}/files` - Lists available output artifacts.
* `GET /api/jobs/{jid}/files/{filename}` - Downloads a specific artifact.
* `GET /api/jobs/{jid}/download` - Downloads the complete `artifacts.zip` result bundle.
* `GET /api/samples/{filename}` - Serves sample test data.

**Status:** Verified structure via codebase inspection and test suite.

## 5. Database Schema
**Current Engine:** SQLite (local) or PostgreSQL via SQLAlchemy `create_all()`.
**Existing Table:** `jobs`
* `id`: String(36), Primary Key
* `name`: String(160)
* `status`: String(24), default 'queued'
* `stage`: String(8)
* `progress`: Float
* `message`: String(2000)
* `created`: Float (timestamp)
* `updated`: Float (timestamp)
* `options`: JSON
* `report`: JSON

**Status:** Verified via schema reflection and `app/db.py`. 

## 6. Behavior That Cannot Be Verified Locally
* **COLMAP / GPU Dense Reconstruction:** Requires a CUDA environment and the COLMAP binary to be present, which is not available in the current local test runner.
* **Custom PT Loading:** Segmentation models via PyTorch requires external model checkpoints not present locally.
* **RQ / Redis Worker Queue:** Running in a purely local thread-pool mode without Redis. The Redis codepaths were not locally executed during this baseline.
