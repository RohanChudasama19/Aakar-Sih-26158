# AAKAR Accuracy Validation Documentation

## Overview

AAKAR performs two separate accuracy-related computations. **These must never be conflated.**

### 1. GPS Alignment Residual (NOT accuracy validation)

Computed in `app/pipeline/georef.py`.
Measures how well reconstructed camera positions fit the GPS trajectory **after**
the Sim(3) transform is fitted to those same GPS/camera pairs.
This is a **fit residual** — by definition, it cannot be used as proof of absolute accuracy.

Reported as: `alignment.rmse_m` in `mission_report.json`

### 2. Independent Spatial Accuracy Validation (this module)

Computed in `app/pipeline/accuracy_validation.py`.
Uses survey-grade checkpoint observations that are **completely independent**
of the alignment fit. These are never used to estimate the georeferencing transform.

Reported in: `outputs/validation/validation_report.json`

---

## Checkpoint CSV Schema

```
checkpoint_id,latitude,longitude,elevation,role[,recon_x,recon_y,recon_z,vertical_datum,reference_accuracy_horizontal_m,reference_accuracy_vertical_m,survey_method]
```

### Required columns

| Column | Type | Description |
|---|---|---|
| `checkpoint_id` | string | Unique identifier. No duplicates. |
| `latitude` | float | WGS84 latitude in decimal degrees (±90) |
| `longitude` | float | WGS84 longitude in decimal degrees (±180) |
| `elevation` | float | Height (in metres). Datum specified via `vertical_datum`. |
| `role` | enum | `CHECKPOINT` = independent validation only. `CONTROL` = excluded from RMSE (alignment placeholder for future use). |

### Optional columns

| Column | Type | Description |
|---|---|---|
| `recon_x`, `recon_y`, `recon_z` | float | Pre-supplied reconstructed point in local UTM frame. Enables Method A (explicit) correspondence. |
| `vertical_datum` | enum | `ELLIPSOIDAL`, `ORTHOMETRIC`, `LOCAL`, or `UNKNOWN` |
| `reference_accuracy_horizontal_m` | float | Stated horizontal accuracy of the survey reference (e.g., 0.02 for 2 cm RTK) |
| `reference_accuracy_vertical_m` | float | Stated vertical accuracy of the survey reference |
| `survey_method` | string | e.g., `RTK_FIXED`, `TOTAL_STATION`, `TLS`, `PPK`, `UNKNOWN` |

### Example

```csv
checkpoint_id,latitude,longitude,elevation,role,recon_x,recon_y,recon_z,vertical_datum,reference_accuracy_horizontal_m,reference_accuracy_vertical_m,survey_method
CP01,47.3769,8.5417,408.2,CHECKPOINT,12.44,8.11,3.85,ELLIPSOIDAL,0.02,0.03,RTK_FIXED
CP02,47.3771,8.5421,409.1,CHECKPOINT,,,UNKNOWN,0.05,0.08,GNSS_FLOAT
GCP01,47.3765,8.5411,407.8,CONTROL,,,ELLIPSOIDAL,0.02,0.03,RTK_FIXED
```

---

## Correspondence Methods

### Method A — Explicit Correspondence (Preferred)

If `recon_x`, `recon_y`, `recon_z` are provided in the CSV, they are used directly
as the reconstructed surface location corresponding to that checkpoint.

This is the most reliable method. It requires the user to identify the corresponding
reconstructed point (e.g., via interactive mesh picking or photogrammetric image marking).

### Method B — Closest Surface Point (Fallback)

If no explicit coordinates are given, the system finds the **closest point on the
reconstructed triangle surface** (not nearest vertex) within a configurable search radius.

**Search radius**: `DEFAULT_CHECKPOINT_SEARCH_RADIUS_M = 2.0 m`
This conservative default is appropriate for a =1 m accuracy target.

**Warning threshold**: `> 0.5 × search_radius` (1.0 m) ? `WEAK_CORRESPONDENCE`

**Limitation**: Closest-surface matching is appropriate only when the surveyed
checkpoint physically corresponds to a visible reconstructed surface. It is NOT
equivalent to manually identified feature correspondence in all situations.

---

## CRS Conversion

All checkpoint coordinates are converted using `pyproj`:

```
WGS84 (lat/lon) ? UTM EPSG:XXXXX (same as reconstruction)
```

The UTM origin is subtracted to produce local UTM frame coordinates matching the
reconstruction frame. Latitude/longitude degrees are never compared directly
to metric XYZ — this would be physically meaningless.

---

## Error Metrics

For each valid CHECKPOINT:

```
?X = local_x_checkpoint - match_x_reconstruction
?Y = local_y_checkpoint - match_y_reconstruction
?Z = local_z_checkpoint - match_z_reconstruction

Horizontal Error = sqrt(?X² + ?Y²)
3D Error = sqrt(?X² + ?Y² + ?Z²)
```

### Aggregate metrics

```
RMSE_X = sqrt(mean(?X²))
RMSE_Y = sqrt(mean(?Y²))
RMSE_Z = sqrt(mean(?Z²))    [only if vertical datums are compatible]
RMSE_HORIZONTAL = sqrt(mean(Horizontal²))
RMSE_3D = sqrt(mean(3D²))   [only if vertical datums are compatible]
mean_3D_error
median_3D_error
max_3D_error
```

---

## Vertical Datum Handling

The reconstruction vertical axis is typically derived from GPS altitude
(ELLIPSOIDAL datum). If a checkpoint uses ORTHOMETRIC height, and both
datums are explicitly known, `RMSE_Z` and `RMSE_3D` are marked as
`NOT_VALIDATED` and `vertical_z_validated = false` is set.

Horizontal RMSE is still computed and reported.

Do not assume GPS altitude, barometric altitude, RTK height, and surveyed
elevation all use the same vertical reference — they do not.

---

## Pass/Fail Rule (SIH Internal)

```
PASSED  iff:  RMSE_3D <= 1.0 m
              AND valid_checkpoint_count >= 4
              AND vertical_z_validated = True
```

The UI always reports **Horizontal RMSE, Vertical RMSE, and 3D RMSE** regardless
of the pass rule outcome, because the SIH problem statement specifies
"spatial accuracy = 1 m" without prescribing a single metric.

---

## Validation States

| State | Meaning |
|---|---|
| `PASSED` | RMSE_3D = 1.0 m with = 4 valid independent checkpoints |
| `FAILED` | RMSE_3D > 1.0 m |
| `NOT_AVAILABLE` | No independent checkpoint CSV provided |
| `NOT_ENOUGH_CHECKPOINTS` | Fewer than 4 valid CHECKPOINT rows |
| `INVALID_REFERENCE` | Bad CRS, missing alignment params, or CSV schema error |

### Per-checkpoint statuses

| Status | Meaning |
|---|---|
| `VALID` | Matched within 50% of search radius |
| `WEAK_CORRESPONDENCE` | Matched but at > 50% of search radius (auto method only) |
| `OUTSIDE_COVERAGE` | No surface within search radius |
| `CONTROL` | CONTROL-role point; excluded from RMSE by design |

---

## Outlier Policy

Outliers are **not silently removed** to improve accuracy metrics.
All checkpoint residuals are computed and reported.
If weak correspondence is detected, it is flagged with `WEAK_CORRESPONDENCE`
and a warning is issued — but the checkpoint remains in the RMSE unless
explicitly outside coverage.

Raw metrics are always reported. If filtering is ever applied in future,
both raw and filtered results must be reported separately.

---

## Real vs Synthetic Data

The validation engine works identically for real and synthetic data.
Synthetic tests only verify engine correctness.

**For the Zurich GPU mission (Step 5):**
- GPS alignment residual: AVAILABLE (0.8244 m fit residual)
- Independent spatial accuracy: `NOT_AVAILABLE` (no survey-grade GCPs supplied)
- SIH =1 m claim: `NOT_AVAILABLE`

This is the correct and honest result. The claim can only be made with
genuine independent survey data.
