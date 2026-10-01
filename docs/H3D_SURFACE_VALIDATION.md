# H3D Hessigheim Surface Validation

**Status**: VERIFIED_REAL_DATA (Engine Only)

## File Roles and Metadata
- `Mar19_test.laz` (Role: **Test/Evaluation Target**): Unclassified raw LiDAR point cloud (Classification: [0]). Contains 82,042,556 points.
- `Mar19_test_GroundTruth.laz` (Role: **Reference Geometry**): Manually annotated LiDAR point cloud (Classification: [0, 1, 2, ..., 10]). Contains exactly 82,042,556 points, identical to the test cloud.

**CRS Validation:**
- Horizontal CRS: EPSG:32632 (UTM Zone 32N)
- Vertical Datum: DHHN2016 (Standard normal heights)

Because the two point clouds contain precisely identical geometry (differentiated only by semantic class labels), this test acts as a **SURFACE_VALIDATION_ENGINE_REAL_DATA_TEST**. It validates the memory limits, sampling determinism, and K-D tree evaluation of the validation engine on a massive real-world dataset. 

It does **NOT** represent `AAKAR_END_TO_END_ACCURACY`, as the test cloud was not photogrammetrically reconstructed from video/images by AAKAR.

## Real Data Metrics (C2C)
Since the geometries are identical, both accuracy and completeness converge toward 0 error.
- **POST_HOC_ICP_USED:** FALSE
- **Test -> GroundTruth (Accuracy):**
  - RMSE_3D: 0.000 m
  - Median: 0.000 m
  - P95: 0.000 m
- **GroundTruth -> Test (Completeness):**
  - Coverage (1.0m): 100.0%

## SIH <= 1m Decision
**Status:** NOT_AVAILABLE
Although the evaluation engine processed the real data seamlessly, the SIH <=1m spatial accuracy target requires an independent verification of an *AAKAR-generated* reconstruction against independent reference data. Because we compared two identical LiDAR clouds (a semantic benchmark), this cannot be cited as photogrammetric accuracy.
