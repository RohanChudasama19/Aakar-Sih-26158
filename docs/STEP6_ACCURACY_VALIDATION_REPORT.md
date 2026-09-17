# Step 6: Independent Spatial Accuracy Validation — Report

## Implementation Status

All components implemented and structurally verified.

---

## What Was Built

### 1. Core Engine — `app/pipeline/accuracy_validation.py`

A standalone module completely separate from `georef.py`. Never called during the Phase-4 alignment fit.

**Key classes/functions:**
| Symbol | Purpose |
|---|---|
| `ValidationStatus` | PASSED / FAILED / NOT_AVAILABLE / NOT_ENOUGH_CHECKPOINTS / INVALID_REFERENCE |
| `CheckpointRole` | CONTROL (excluded from RMSE) / CHECKPOINT (independent validation only) |
| `CorrespondenceMethod` | EXPLICIT (recon_x/y/z) / CLOSEST_SURFACE (triangle projection) |
| `CheckpointStatus` | VALID / OUTSIDE_COVERAGE / WEAK_CORRESPONDENCE / INVALID_VERTICAL_DATUM |
| `VerticalDatum` | ELLIPSOIDAL / ORTHOMETRIC / LOCAL / UNKNOWN |
| `parse_checkpoint_csv()` | Validates schema, deduplicates IDs, checks lat/lon ranges |
| `project_checkpoints()` | WGS84 → UTM projected coordinates → local UTM frame |
| `find_correspondence()` | Method A (explicit) preferred; Method B (closest triangle surface) fallback |
| `compute_residuals()` | Per-checkpoint ΔX/ΔY/ΔZ/horizontal/3D — CONTROL excluded by design |
| `compute_rmse()` | RMSE_X/Y/Z/HORIZONTAL/3D, mean/median/max |
| `decide_status()` | RMSE_3D ≤ 1.0 m AND n ≥ 4 → PASSED |
| `validate()` | Top-level entry point returning full report dict |

### 2. API Endpoints — `app/main.py`

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/jobs/{jid}/validation` | GET | Returns validation_report.json or NOT_AVAILABLE |
| `/api/jobs/{jid}/checkpoints` | POST | Upload independent checkpoints CSV (NOT for alignment) |
| `/api/jobs/{jid}/run-validation` | POST | Trigger validation computation |

### 3. UI — `web/app.js`

The Validation tab now shows two clearly separate panels:

**Panel 1 — Alignment Quality:**
- GPS Alignment Residual (RMSE)
- Inliers / Samples
- Metric State
- Disclaimer: *"Sim(3) fit residual — NOT independent spatial accuracy"*

**Panel 2 — Independent Spatial Validation:**
- Fetches `/api/jobs/{jid}/validation` dynamically
- Shows NOT AVAILABLE / PASSED / FAILED / NOT_ENOUGH_CHECKPOINTS status
- Displays RMSE_H, RMSE_V, RMSE_3D table when results exist
- Per-checkpoint residuals table with colour-coded status
- Checkpoint CSV upload with explicit label: *"Used only for validation, not for georeferencing"*

---

## Verification Results

### Browser E2E:
NOT_EXECUTED

**Reason**: Browser binary installation/download unavailable due to CDN/network timeout in the CI/Agent environment. Screenshots (`no_checkpoints.png`, `passed.png`, `failed.png`, `not_enough.png`) were NOT captured from a real browser rendering. 

### API E2E:
VERIFIED

**Method**: API contract verification via `httpx.AsyncClient` against the live FastAPI/uvicorn application.

### Real Independent Reference Data:
NOT_AVAILABLE

### SIH ≤1 m:
NOT_AVAILABLE

### Alignment Residual:
Zurich GPU validation mission: `0.9324 m` (fit residual, NOT independent accuracy).

### Independent Accuracy:
NOT_AVAILABLE

### Coordinate Frame:
local UTM frame (WGS84 → UTM projected coordinates → subtract local origin).

### Final commit hash:
(Will be supplied after commit)

---

## Tests

### Accuracy Validation Tests — `tests/test_accuracy_validation.py`

| Test | Result |
|---|---|
| `test_basic_residual_math` | PASSED |
| `test_rmse_computation` | PASSED |
| `test_pass_threshold` | PASSED |
| `test_fail_threshold` | PASSED |
| `test_not_enough_checkpoints` | PASSED |
| `test_control_checkpoint_separation` | PASSED |
| `test_crs_roundtrip` | PASSED |
| `test_outside_coverage_flagged` | PASSED |
| `test_duplicate_id_rejected` | PASSED |
| `test_invalid_lat_rejected` | PASSED |
| `test_vertical_datum_mismatch` | PASSED |
| `test_explicit_correspondence` | PASSED |
| `test_closest_surface_uses_triangle` | PASSED |
| `test_validation_api_no_checkpoints` | PASSED |
| `test_validation_api_with_report` | PASSED |
| `test_weak_correspondence_flagged` | PASSED |
| `test_closest_point_on_triangle_geometry` | PASSED |

**Total: 17/17 PASSED**

### Full Regression

| Suite | Count | Result |
|---|---|---|
| All tests/ | 100 | 100 PASSED |
| ruff (accuracy_validation.py + main.py) | — | All checks passed |
| mypy (new files) | — | No errors |

---

## Limitations

1. **CLOSEST_SURFACE** correspondence depends on the reconstructed surface existing where the checkpoint was surveyed. It is not equivalent to manually identified feature correspondence.
2. **Vertical datum**: GPS altitude (ELLIPSOIDAL) is commonly different from surveyed orthometric height. Mixed datums suppress RMSE_3D.
3. **Search radius**: 2.0 m default. Tighter than 5 m given the ≤1 m accuracy target; still generous for coarse auto-matching.
4. **No real checkpoints**: Until survey-grade GCPs are provided for a real mission, the ≤1 m claim cannot be made.
