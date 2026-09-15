# Phase 1: Reconstruction Readiness and Input Quality Gate

## Objective
Implement a lightweight, explainable quality gate before expensive 3D reconstruction begins. Assess drone mission readiness (READY, WARNING, NOT_READY) based on frame sampling, geometric overlap, blur, exposure, and telemetry validity.

## Key Decisions & Architecture
- **Stratified Temporal Sampling:** Instead of uniformly analyzing the entire video or a fixed count, the video is sampled inside temporal windows (e.g. 5-second windows) to ensure continuous timeline coverage while keeping the gate fast.
- **Metric Normalization:** Intrinsics, when available, are scaled to the standardized analysis resolution (default 960px). Parallax is calculated as the angular difference of normalized rays. If intrinsics are absent, a pixel-based parallax proxy is used.
- **Geometric Checks:** Instead of simple pixel displacement or just Fundamental Matrix, we use Homography (for pure rotation/planar detection) and Essential Matrix when intrinsics are provided. Overlap is estimated via SIFT matching on temporal pairs.
- **Dataset Connectivity:** Pairs of frames forming geometric inliers build an overlap graph. Connected components are determined (using BFS) to measure whether the flight dataset is entirely connected or suffers from disjoint sections.
- **Explainability:** Generates a structured `cv_quality_report.json` containing numerical evidence, blocking reasons, warnings, and recommendations, along with a human-readable `cv_quality_report.txt`.
- **Database Schema:** Added `readiness_status`, `readiness_score`, and `readiness_report_path` to the SQLite Job schema via an Alembic migration. When a job fails readiness, it is marked `RECONSTRUCTION_BLOCKED`.
