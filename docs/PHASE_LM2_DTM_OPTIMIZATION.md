# Phase L/M2: DTM Tiling and Quality Optimization

## Algorithm
Tiled Multi-scale Progressive Morphological Filter (PMF).

## Train/Val Protocol
- **Train/val data used:** None (No local train/val data was available).
- **Parameters used:** Canonical defaults drawn from PMF literature (windows_m=[3.0, 10.0, 30.0], init_dh=0.3, slope_threshold=0.15, max_dh=3.0).
- **Test leakage protection:** TRUE (Mar19_test.laz geometry evaluated completely independently from the GroundTruth label array).

## Tiling Protocol
- Mode: **TILED**
- Tile size: 200.0 m
- Tile overlap: 30.0 m
- Tile count: 6
- Result: Verified deterministic spatial tiling avoids seam artifacts via localized boundary overlap discarding.

## Performance
- **Peak RAM:** 5413 MB
- **Runtime:** 67.62 seconds (processing 82 million points)
- **Temporary Disk:** 0 MB
- **Output Files:** DSM ~4.5MB, DTM ~4.5MB, Coverage Mask ~1.5MB

## Ground Classification Accuracy
- **Precision:** 0.344 (Baseline: 0.346)
- **Recall:** 0.959 (Baseline: 0.910)
- **F1 Score:** 0.506 (Baseline: 0.501)
- **IoU:** 0.339 (Baseline: 0.335)

## DTM Height Quality
- **RMSE_Z:** 1.428 m (Baseline: 1.691 m)
- **MAE_Z:** 0.351 m (Baseline: 0.456 m)
- **Median Z Error:** 0.034 m
- **P95 Error:** 1.830 m
- **Bias:** -0.351 m

## Coverage States
The single 100% monolithic value was audited and correctly partitioned:
- **Observed Ground:** 20.2%
- **Interpolated (Small Gaps):** 22.5%
- **Unobserved (NoData):** 57.2%

## SIH <=1m Status
**NOT_AVAILABLE**. (H3D measures the terrain extraction engine capability, but true SIH 1m spatial compliance still requires an independent photogrammetry reconstruction comparison).
