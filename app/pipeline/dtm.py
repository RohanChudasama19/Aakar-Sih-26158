import numpy as np
from rasterio.transform import from_origin
from scipy.interpolate import griddata
from scipy.ndimage import distance_transform_edt, grey_opening

# Coverage constants
COV_UNOBSERVED = 0
COV_OBSERVED = 1
COV_INTERPOLATED = 2


def progressive_morphological_filter(
    z_grid: np.ndarray, resolution: float, windows_m: list[float], init_dh: float, slope: float, max_dh: float
) -> np.ndarray:
    """
    Multi-scale Progressive Morphological Filter (PMF).
    """
    valid_mask = ~np.isnan(z_grid)
    if not np.any(valid_mask):
        return z_grid.copy()

    # Fill grid for morphology
    coords = np.array(np.nonzero(valid_mask)).T
    values = z_grid[valid_mask]
    grid_r, grid_c = np.mgrid[0 : z_grid.shape[0], 0 : z_grid.shape[1]]

    # Base surface
    surf = griddata(coords, values, (grid_r, grid_c), method="nearest")

    prev_surf = surf.copy()

    # Progressively open
    for i, w_m in enumerate(windows_m):
        w_px = max(3, int(w_m / resolution))
        # Morphological opening
        opened = grey_opening(prev_surf, size=(w_px, w_px))

        # Calculate allowed height difference
        # dh = initial_dh + slope * (window_size)
        dh = min(init_dh + slope * w_m, max_dh)

        # Any point in prev_surf that is strictly higher than opened + dh is NOT ground,
        # so we bring the surface down to `opened` in those areas.
        # But wait, PMF normally operates on points. Here we operate on the raster.
        # So we cap the surface elevation.
        # If the current surface is too high above the opened surface, it's a building/tree.
        # We replace those pixels with the opened surface.
        non_ground_mask = (prev_surf - opened) > dh
        prev_surf = np.where(non_ground_mask, opened, prev_surf)

    return prev_surf


def generate_dsm_dtm(
    points: np.ndarray,
    resolution: float = 1.0,
    windows_m: list[float] = [3.0, 10.0, 30.0],
    init_dh: float = 0.3,
    slope_threshold: float = 0.15,
    max_dh: float = 2.5,
    max_gap_m: float = 30.0,
    bounds: tuple | None = None,
):
    if len(points) == 0:
        return None

    x = points[:, 0]
    y = points[:, 1]
    z = points[:, 2]

    if bounds is None:
        min_x, max_x = np.min(x), np.max(x)
        min_y, max_y = np.min(y), np.max(y)
    else:
        min_x, max_x, min_y, max_y = bounds

    # Raster dimensions
    width = int(np.ceil((max_x - min_x) / resolution))
    height = int(np.ceil((max_y - min_y) / resolution))

    if width <= 0 or height <= 0:
        return None

    # Map points to grid cells
    col = np.clip(np.floor((x - min_x) / resolution).astype(int), 0, width - 1)
    row = np.clip(np.floor((max_y - y) / resolution).astype(int), 0, height - 1)

    # 1. DSM (Max Z)
    sort_idx = np.argsort(z)
    col_sorted = col[sort_idx]
    row_sorted = row[sort_idx]
    z_sorted = z[sort_idx]

    dsm = np.full((height, width), np.nan, dtype=np.float32)
    dsm[row_sorted, col_sorted] = z_sorted

    # 2. Min Grid
    min_grid = np.full((height, width), np.nan, dtype=np.float32)

    min_grid[row_sorted[::-1], col_sorted[::-1]] = z_sorted[::-1]

    # 3. PMF (Multi-scale morphology)
    bare_earth_est = progressive_morphological_filter(min_grid, resolution, windows_m, init_dh, slope_threshold, max_dh)

    # 4. Filter Ground Points
    pt_bare_z = bare_earth_est[row, col]
    # Rejection of elevated flat surfaces (roofs):
    # The PMF lowers `pt_bare_z` to the ground level beneath buildings.
    # So `z - pt_bare_z` will be large (e.g. 5m) for roof points.
    # Sloped terrain points will be within `max_dh` (or slope threshold).
    # We use a final threshold based on local PMF surface.
    is_ground = z <= pt_bare_z + 0.5

    ground_pts = points[is_ground]

    # 5. DTM Interpolation
    gx = ground_pts[:, 0]
    gy = ground_pts[:, 1]
    gz = ground_pts[:, 2]

    gcol = np.clip(np.floor((gx - min_x) / resolution).astype(int), 0, width - 1)
    grow = np.clip(np.floor((max_y - gy) / resolution).astype(int), 0, height - 1)

    dtm_sparse = np.full((height, width), np.nan, dtype=np.float32)
    sort_idx_g = np.argsort(gz)[::-1]
    dtm_sparse[grow[sort_idx_g], gcol[sort_idx_g]] = gz[sort_idx_g]

    valid_g_mask = ~np.isnan(dtm_sparse)

    # Initialize coverage mask
    coverage_mask = np.full((height, width), COV_UNOBSERVED, dtype=np.uint8)
    coverage_mask[valid_g_mask] = COV_OBSERVED

    grid_r, grid_c = np.mgrid[0:height, 0:width]

    dtm = np.full((height, width), np.nan, dtype=np.float32)
    if np.any(valid_g_mask):
        gcoords = np.array(np.nonzero(valid_g_mask)).T
        gvalues = dtm_sparse[valid_g_mask]

        # Interpolate
        if len(gvalues) > 3:
            dtm = griddata(gcoords, gvalues, (grid_r, grid_c), method="linear")
            nan_mask = np.isnan(dtm)
            if np.any(nan_mask):
                dtm_nearest = griddata(gcoords, gvalues, (grid_r, grid_c), method="nearest")
                dtm[nan_mask] = dtm_nearest[nan_mask]
        else:
            dtm = griddata(gcoords, gvalues, (grid_r, grid_c), method="nearest")

    # Mask out gaps > max_gap_m
    max_gap_px = max_gap_m / resolution
    if np.any(valid_g_mask):
        dist = distance_transform_edt(~valid_g_mask)
        interp_mask = (dist > 0) & (dist <= max_gap_px)
        coverage_mask[interp_mask] = COV_INTERPOLATED

        dtm[coverage_mask == COV_UNOBSERVED] = np.nan
        dsm[coverage_mask == COV_UNOBSERVED] = np.nan

    transform = from_origin(min_x, max_y, resolution, resolution)

    return {
        "dtm": dtm,
        "dsm": dsm,
        "transform": transform,
        "is_ground": is_ground,
        "coverage_mask": coverage_mask,
        "width": width,
        "height": height,
        "bounds": (min_x, max_x, min_y, max_y),
    }


def generate_dsm_dtm_tiled(
    points: np.ndarray, resolution: float = 1.0, tile_size_m: float = 200.0, overlap_m: float = 40.0, **kwargs
):
    """
    Process DTM generation using deterministic spatial tiling to guarantee memory safety.
    """
    if len(points) == 0:
        return None

    x = points[:, 0]
    y = points[:, 1]

    min_x, max_x = np.min(x), np.max(x)
    min_y, max_y = np.min(y), np.max(y)

    width = int(np.ceil((max_x - min_x) / resolution))
    height = int(np.ceil((max_y - min_y) / resolution))

    final_dtm = np.full((height, width), np.nan, dtype=np.float32)
    final_dsm = np.full((height, width), np.nan, dtype=np.float32)
    final_cov = np.full((height, width), COV_UNOBSERVED, dtype=np.uint8)
    final_is_ground = np.zeros(len(points), dtype=bool)

    # Pre-calculate tile boundaries
    x_steps = np.arange(min_x, max_x, tile_size_m)
    y_steps = np.arange(min_y, max_y, tile_size_m)

    tile_count = 0

    for tx in x_steps:
        for ty in y_steps:
            t_min_x = tx - overlap_m
            t_max_x = tx + tile_size_m + overlap_m
            t_min_y = ty - overlap_m
            t_max_y = ty + tile_size_m + overlap_m

            # Select points in extended tile
            mask = (x >= t_min_x) & (x < t_max_x) & (y >= t_min_y) & (y < t_max_y)
            tile_pts = points[mask]

            if len(tile_pts) == 0:
                continue

            # Process extended tile
            t_res = generate_dsm_dtm(
                tile_pts, resolution=resolution, bounds=(t_min_x, t_max_x, t_min_y, t_max_y), **kwargs
            )

            if t_res is None:
                continue

            tile_count += 1

            # Merge tile into global raster, stripping overlap margins
            # We only keep the inner bounding box [tx, tx + tile_size_m] x [ty, ty + tile_size_m]

            # Global indices for inner bounding box
            g_c_min = int(round((tx - min_x) / resolution))
            g_c_max = int(round((tx + tile_size_m - min_x) / resolution))
            g_r_max = int(round((max_y - ty) / resolution))
            g_r_min = int(round((max_y - (ty + tile_size_m)) / resolution))

            g_c_min = max(0, g_c_min)
            g_c_max = min(width, g_c_max)
            g_r_min = max(0, g_r_min)
            g_r_max = min(height, g_r_max)

            # Local indices for inner bounding box
            l_c_min = int(round((tx - t_min_x) / resolution))
            l_c_max = l_c_min + (g_c_max - g_c_min)
            l_r_min = int(round((t_max_y - (ty + tile_size_m)) / resolution))
            l_r_max = l_r_min + (g_r_max - g_r_min)

            # Bounds protection
            l_c_max = min(t_res["width"], l_c_max)
            l_r_max = min(t_res["height"], l_r_max)
            # Adjust global bounds to match actual local slice sizes if truncated
            g_c_max = g_c_min + (l_c_max - l_c_min)
            g_r_max = g_r_min + (l_r_max - l_r_min)

            if (l_r_max <= l_r_min) or (l_c_max <= l_c_min):
                continue

            final_dtm[g_r_min:g_r_max, g_c_min:g_c_max] = t_res["dtm"][l_r_min:l_r_max, l_c_min:l_c_max]
            final_dsm[g_r_min:g_r_max, g_c_min:g_c_max] = t_res["dsm"][l_r_min:l_r_max, l_c_min:l_c_max]
            final_cov[g_r_min:g_r_max, g_c_min:g_c_max] = t_res["coverage_mask"][l_r_min:l_r_max, l_c_min:l_c_max]

            # For boolean array is_ground, we only want to update the original point indices
            # that fall STRICTLY inside the non-overlap region to avoid double-counting or border effects.
            inner_mask = (
                (tile_pts[:, 0] >= tx)
                & (tile_pts[:, 0] < tx + tile_size_m)
                & (tile_pts[:, 1] >= ty)
                & (tile_pts[:, 1] < ty + tile_size_m)
            )

            global_indices = np.where(mask)[0][inner_mask]
            final_is_ground[global_indices] = t_res["is_ground"][inner_mask]

    transform = from_origin(min_x, max_y, resolution, resolution)

    return {
        "dtm": final_dtm,
        "dsm": final_dsm,
        "transform": transform,
        "is_ground": final_is_ground,
        "coverage_mask": final_cov,
        "width": width,
        "height": height,
        "bounds": (min_x, max_x, min_y, max_y),
        "tile_count": tile_count,
    }
