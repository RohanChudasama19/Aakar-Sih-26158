# GCP Alignment Validation

AeroRecon correctly separates CONTROL points from CHECKPOINT points at the architecture level.

## CONTROL Alignment
- `CONTROL` points are used to establish Metric Scale and Georeferencing.
- At least 4 non-collinear, non-clustered controls are required for full 3D alignment.
- A robust Umeyama Sim(3) fit is performed, weighted by the reference inverse variance (`reference_accuracy_m`).
- Outputs `gcp_alignment_report.json` containing the fit residual `CONTROL_FIT_RMSE` and the subset of robust inliers.

## CHECKPOINT Leakage Protection
- The alignment algorithm (`fit_control_alignment`) explicitly filters the list, completely excluding any point marked `CHECKPOINT`.
- Checkpoint coordinates never influence the scale, rotation, or translation of the model.

## Vertical Datum Safety
- If CONTROL points lack a consistent vertical datum, the system safely falls back to `GCP_HORIZONTAL_ONLY`.

## Current Status
- `GCP_ENGINE = IMPLEMENTED_SYNTHETICALLY_VERIFIED`
- We await a real surveyed dataset to establish `VERIFIED_REAL_DATA`.
