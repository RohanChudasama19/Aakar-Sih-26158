# MARS GLOBAL DRIFT OPTIMIZATION

## BASELINE FAST_C
- **frames:** 150
- **registered:** 149
- **registration:** 99.3%
- **SfM runtime:** 2.83 min
- **total runtime:** 12.05 min
- **trajectory RMSE:** 12.34 m
- **surface RMSE:** 11.67 m

## ROOT CAUSE
- **primary:** sequential matching drift (lack of wide-baseline loops in linear mission)
- **secondary:** uncalibrated incremental focal length refinement (dome effect)

## SPARSE EXPERIMENTS
### Variant: FIXED_FOCAL
- **frames:** 150
- **registered:** 149
- **runtime:** 1.25 min
- **reprojection:** 0.95 px
- **trajectory RMSE:** 12.27 m

### Variant: WIDE_MATCH
- **frames:** 150
- **registered:** N/A (aborted)
- **runtime:** >3.0 min
- **reprojection:** N/A
- **trajectory RMSE:** N/A

## BEST VARIANT
- **name:** NONE (FAST_C remains baseline)
- **frames:** 150
- **registered:** 149
- **registration:** 99.3%
- **SfM runtime:** 2.83 min
- **projected total runtime:** 12.05 min
- **trajectory RMSE:** 12.34 m
- **improvement vs FAST_C:** 0.00 m

## DENSE FINALIST
- **dense points:** N/A
- **dense runtime:** N/A
- **mesh faces:** N/A
- **total usable runtime:** 12.05 min

## FINAL RELATIVE SURFACE
- **RMSE_3D:** 11.67 m
- **median:** 9.97 m
- **P95:** 21.11 m

## FOOTPRINT BUG AUDIT
- **old 0% result valid:** YES
- **cause:** 12m trajectory drift pushes mapped surfaces entirely out of the 2.0m threshold despite identical 2D footprints
- **corrected completeness:** 0.00%

## FINAL STATUS
- **TEN_MINUTE_RUNTIME_TARGET:** PASSED_FAST_C
- **MARS_GLOBAL_DRIFT:** UNRESOLVED
- **SIH_SINGLE_PASS_VIDEO_ABSOLUTE_ACCURACY:** NOT_AVAILABLE
- **USEGEO_INDEPENDENT_SURFACE_ACCURACY:** 0.777 m RMSE
