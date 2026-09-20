import numpy as np
from rasterio.transform import from_origin
from scipy.interpolate import griddata
from scipy.ndimage import binary_dilation, grey_opening


def generate_dsm_dtm(
    points: np.ndarray,
    resolution: float = 0.5,
    slope_threshold: float = 1.0,
    window_size_m: float = 15.0,
    max_gap_m: float = 20.0,
):
    """
    Generate Bare-Earth DTM and Top-Surface DSM using a simple grid-based
    morphological filter.

    1. Grid the points into 2D cells.
    2. DSM = max Z per cell.
    3. Min grid = min Z per cell.
    4. Morphological opening on Min grid to estimate bare earth (remove buildings/trees).
    5. Filter original points based on distance to bare earth estimate.
    6. Interpolate ground points to fill gaps up to max_gap_m.
    """
    print(f"Generating DTM/DSM for {len(points)} points...")
    if len(points) == 0:
        return None

    x = points[:, 0]
    y = points[:, 1]
    z = points[:, 2]

    min_x, max_x = np.min(x), np.max(x)
    min_y, max_y = np.min(y), np.max(y)

    # Raster dimensions
    width = int(np.ceil((max_x - min_x) / resolution))
    height = int(np.ceil((max_y - min_y) / resolution))

    # Map points to grid cells
    col = np.clip(np.floor((x - min_x) / resolution).astype(int), 0, width - 1)
    # Origin is usually top-left in rasterio, so invert Y
    row = np.clip(np.floor((max_y - y) / resolution).astype(int), 0, height - 1)

    # 1. DSM
    # We use a trick: lexsort by Z, then assign to grid, so the last assignment is max Z
    sort_idx = np.argsort(z)
    col_sorted = col[sort_idx]
    row_sorted = row[sort_idx]
    z_sorted = z[sort_idx]

    dsm = np.full((height, width), np.nan, dtype=np.float32)
    dsm[row_sorted, col_sorted] = z_sorted

    # 2. Min Grid
    # First assignment in sorted is min Z
    min_grid = np.full((height, width), np.nan, dtype=np.float32)

    # Reverse sort for min assignment trick (first is largest, last is smallest)
    sort_idx_rev = sort_idx[::-1]
    min_grid[row[sort_idx_rev], col[sort_idx_rev]] = z[sort_idx_rev]

    # Fill nan in min_grid via nearest interpolation just for the filter
    valid_mask = ~np.isnan(min_grid)
    if not np.any(valid_mask):
        return None

    coords = np.array(np.nonzero(valid_mask)).T
    values = min_grid[valid_mask]

    grid_r, grid_c = np.mgrid[0:height, 0:width]

    print("Interpolating base min-grid...")
    # nearest is fast
    min_grid_filled = griddata(coords, values, (grid_r, grid_c), method="nearest")

    # 3. Morphological opening
    # Window size in pixels
    w_px = max(3, int(window_size_m / resolution))
    print(f"Applying morphological opening with window size {w_px} px...")

    # grey_opening removes peaks (buildings/trees) that are smaller than window size
    bare_earth_est = grey_opening(min_grid_filled, size=(w_px, w_px))

    # 4. Filter ground points
    # Points are ground if their Z is within threshold of bare earth estimate
    pt_bare_z = bare_earth_est[row, col]
    is_ground = z <= pt_bare_z + slope_threshold

    ground_pts = points[is_ground]
    print(f"Identified {len(ground_pts)} ground points ({len(ground_pts) / len(points) * 100:.1f}%)")

    # 5. DTM Interpolation
    gx = ground_pts[:, 0]
    gy = ground_pts[:, 1]
    gz = ground_pts[:, 2]
    gcol = np.clip(np.floor((gx - min_x) / resolution).astype(int), 0, width - 1)
    grow = np.clip(np.floor((max_y - gy) / resolution).astype(int), 0, height - 1)

    dtm_sparse = np.full((height, width), np.nan, dtype=np.float32)
    # just assign mean or min. let's assign min ground Z per cell
    sort_idx_g = np.argsort(gz)[::-1]
    dtm_sparse[grow[sort_idx_g], gcol[sort_idx_g]] = gz[sort_idx_g]

    valid_g_mask = ~np.isnan(dtm_sparse)
    gcoords = np.array(np.nonzero(valid_g_mask)).T
    gvalues = dtm_sparse[valid_g_mask]

    print("Interpolating final DTM (linear)...")
    dtm = griddata(gcoords, gvalues, (grid_r, grid_c), method="linear")

    # Fill remaining NaNs with nearest, but mask out large gaps
    nan_mask = np.isnan(dtm)
    if np.any(nan_mask):
        print("Filling remaining gaps with nearest...")
        dtm_nearest = griddata(gcoords, gvalues, (grid_r, grid_c), method="nearest")
        dtm[nan_mask] = dtm_nearest[nan_mask]

    # Mask out gaps larger than max_gap_m
    max_gap_px = int(max_gap_m / resolution)
    observed_mask = valid_g_mask.copy()
    # Dilate observed cells by max_gap_px
    if max_gap_px > 0:
        coverage_mask = binary_dilation(observed_mask, iterations=max_gap_px)
    else:
        coverage_mask = observed_mask

    dtm[~coverage_mask] = np.nan

    # also mask DSM
    dsm_obs_mask = ~np.isnan(dsm)
    if max_gap_px > 0:
        dsm_cov = binary_dilation(dsm_obs_mask, iterations=max_gap_px)
    else:
        dsm_cov = dsm_obs_mask

    dsm[~dsm_cov] = np.nan

    transform = from_origin(min_x, max_y, resolution, resolution)

    return {
        "dtm": dtm,
        "dsm": dsm,
        "transform": transform,
        "is_ground": is_ground,
        "coverage_mask": coverage_mask,
        "width": width,
        "height": height,
    }
