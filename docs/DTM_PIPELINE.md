# AeroRecon DTM Pipeline

## Architecture
The Digital Terrain Model (DTM) pipeline produces bare-earth rasters from raw or classified point clouds. The engine relies solely on **geometric ground filtering**, ensuring true generalization without mandatory dependence on semantic deep learning predictions.

## Methodology: Grid-Based Morphological Filtering
A robust pseudo-Progressive Morphological Filter (PMF) is applied:
1. **Min-Grid Rasterization**: The point cloud is quantized into a 2D spatial grid (default 1.0m resolution). The lowest Z value is stored in each grid cell.
2. **Morphological Opening**: A greyscale morphological opening (erosion followed by dilation) is applied to the minimum grid using a parameterized window size. This aggressively removes peaks (such as buildings, vehicles, and tree canopies) that are smaller than the window, leaving an estimated bare-earth surface.
3. **Slope-Aware Thresholding**: Points are compared to the bare-earth estimate. If a point falls within a configured vertical tolerance (accounting for natural local slope), it is classified as `OBSERVED_GROUND`.
4. **Interpolation**: The identified ground points are rasterized. Missing cells are interpolated using linear or nearest-neighbor logic.
5. **Coverage Masking**: Extrapolated regions exceeding a `max_gap_m` threshold are masked as `NO_DATA` to prevent inventing imaginary terrain over large unsupported expanses.

## Outputs
- `dtm.tif`: The Bare-Earth terrain model.
- `dsm.tif`: The Top-Surface model (including canopy/roofs).
- `dtm_coverage.tif`: A boolean/confidence mask tracking where true ground data was observed versus interpolated.
