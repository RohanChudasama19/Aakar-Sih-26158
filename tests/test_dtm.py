import numpy as np

from app.pipeline.dtm import COV_INTERPOLATED, COV_OBSERVED, COV_UNOBSERVED, generate_dsm_dtm, generate_dsm_dtm_tiled


def test_dtm_flat_ground_and_building():
    gx, gy = np.mgrid[0:10, 0:10]
    ground = np.column_stack((gx.ravel(), gy.ravel(), np.zeros(100)))
    bx, by = np.mgrid[3:7, 3:7]
    building = np.column_stack((bx.ravel(), by.ravel(), np.full(16, 10.0)))
    pts = np.vstack((ground, building))
    res = generate_dsm_dtm(
        pts, resolution=1.0, windows_m=[3.0, 5.0], init_dh=0.3, slope_threshold=0.2, max_dh=2.0, max_gap_m=5.0
    )
    is_ground = res["is_ground"]
    assert np.all(is_ground[:100])
    assert not np.any(is_ground[100:])
    assert np.nanmax(res["dsm"]) == 10.0
    assert np.nanmax(res["dtm"]) == 0.0


def test_dtm_slope_preserved():
    gx, gy = np.mgrid[0:10, 0:10]
    gz = gx * 0.5
    ground = np.column_stack((gx.ravel(), gy.ravel(), gz.ravel()))
    res = generate_dsm_dtm(ground, resolution=1.0, windows_m=[3.0], init_dh=0.5, slope_threshold=1.0)
    assert np.all(res["is_ground"])


def test_dtm_tiled_consistency():
    gx, gy = np.mgrid[0:30, 0:30]
    ground = np.column_stack((gx.ravel(), gy.ravel(), np.zeros(900)))
    res_full = generate_dsm_dtm(ground, resolution=1.0)
    res_tiled = generate_dsm_dtm_tiled(ground, resolution=1.0, tile_size_m=10.0, overlap_m=5.0)
    assert res_tiled["tile_count"] > 1
    assert np.allclose(res_full["dtm"], res_tiled["dtm"], equal_nan=True)
    assert np.array_equal(res_full["is_ground"], res_tiled["is_ground"])


def test_coverage_states():
    pts = np.array([[0, 0, 0], [10, 10, 0], [20, 20, 0]], dtype=float)
    res = generate_dsm_dtm(pts, resolution=1.0, max_gap_m=3.0)
    cov = res["coverage_mask"]
    assert COV_OBSERVED in cov
    assert COV_INTERPOLATED in cov
    assert COV_UNOBSERVED in cov
    assert np.isnan(res["dtm"][0, 5])
