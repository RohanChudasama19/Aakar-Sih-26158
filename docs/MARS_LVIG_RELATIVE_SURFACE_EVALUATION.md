# MARS-LVIG RELATIVE SURFACE EVALUATION

## 1. OBJECTIVE
This evaluation is a diagnostic, alignment-assisted comparison between the AAKAR FAST_C dense reconstruction and the HKairport `cloud_merged.ply`.
**IMPORTANT:** This evaluation measures relative shape/geometry quality only. It is NOT an independent absolute accuracy metric.

## 2. ALIGNMENT SOURCE
- **Source:** Trajectory correspondence (AAKAR vs UAVScenes metadata)
- **Matched cameras:** 147
- **Type:** Umeyama (Sim3)
- **Scale:** 1.001
- **Trajectory fit RMSE:** 12.34 m

## 3. TRAJECTORY-ALIGNED SURFACE METRICS
(AAKAR -> Reference distances)
- **RMSE_3D:** 11.67 m
- **MAE:** 10.31 m
- **Median:** 9.97 m
- **P95:** 21.11 m
- **P99:** 25.00 m
- **Max:** 32.86 m

## 4. BBOX_CROPPED_REFERENCE_TO_RECONSTRUCTION_COVERAGE
(Reference -> AAKAR, footprint: 3D bounding box + 20m buffer)
- **Within 0.25m:** 0.04%
- **Within 0.50m:** 0.15%
- **Within 1.00m:** 0.47%
- **Within 2.00m:** 1.44%

## 5. ICP DIAGNOSTIC ONLY
- **Used:** YES (After trajectory alignment)
- **RMSE before:** 11.67 m
- **RMSE after (inlier):** 1.10 m
- **Fitness:** 0.32
*After reference-assisted ICP, overlapping inliers achieved 1.10 m RMSE with fitness 0.32. This indicates that portions of the reconstructed geometry exhibit local geometric similarity, but the result is reference-fitted and cannot be used as global, independent, or SIH absolute accuracy.*

## 6. OBSERVED GEOMETRY ISSUES
- **SYSTEMATIC_VERTICAL_ERROR:** NOT_EVALUATED
- **Scale drift:** Minimal (Sim3 scale = 1.001).
- **Warping / local deformation:** Noticeable uncalibrated SfM trajectory drift (12.34m) creates a bowing effect across the 10-minute flight.
- **Missing geometry:** Thin structures and some transparent roofs are missing.

## 7. CLASSIFICATION
**MARS_GLOBAL_RELATIVE_SURFACE_SHAPE = WEAK**

## 8. EXPLANATION
- FAST_C achieved the required runtime goal (12.05 min).
- FAST_C successfully registered 149/150 selected frames.
- Scale is close to unity after trajectory fit (1.001).
- However, long-baseline global trajectory deformation is large (12.34m).
- This produces large global surface misregistration (11.67m RMSE).
- ICP substantially reduces inlier error (1.10m), suggesting local surface similarity in overlapping regions, but ICP is reference-assisted and cannot prove independent accuracy.
- Therefore, the principal remaining reconstruction weakness is **GLOBAL DRIFT / DEFORMATION** across the 10-minute single-pass mission.
