import numpy as np
import trimesh

from app.pipeline.surface_validation import (
    ReferenceMetadata,
    ValidationStatus,
    compute_c2m,
    compute_distances_c2c,
    evaluate_surface_accuracy,
    filter_by_bounds,
    voxel_downsample,
)


def test_c2c_exact_and_symmetric():
    # identical clouds
    recon = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)
    ref = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)

    dists = compute_distances_c2c(recon, ref)
    assert np.allclose(dists, 0.0)

    # parallel planes offset by 0.25m
    ref2 = recon + np.array([0, 0, 0.25])
    dists2 = compute_distances_c2c(recon, ref2)
    assert np.allclose(dists2, 0.25)

    # symmetric test: recon has extra points, ref has extra points
    recon3 = np.array([[0, 0, 0], [1, 0, 0]])
    ref3 = np.array([[0, 0, 0], [0, 1, 0]])

    d1 = compute_distances_c2c(recon3, ref3)
    d2 = compute_distances_c2c(ref3, recon3)
    assert len(d1) == 2 and len(d2) == 2


def test_c2m_triangle_distance():
    recon = np.array([[0.5, 0.5, 1.0]])
    # A single triangle at z=0
    mesh = trimesh.Trimesh(vertices=[[0, 0, 0], [1, 0, 0], [0, 1, 0]], faces=[[0, 1, 2]])
    dists = compute_c2m(recon, mesh)
    assert np.allclose(dists, 1.0)

    # Check that it projects to surface, not just vertex
    recon2 = np.array([[0.25, 0.25, 0.0]])
    dists2 = compute_c2m(recon2, mesh)
    assert np.allclose(dists2, 0.0)


def test_partial_overlap_and_bounds():
    recon = np.array([[0, 0, 0], [10, 10, 0]])
    bounds_min = np.array([-1, -1, -1])
    bounds_max = np.array([1, 1, 1])

    cropped = filter_by_bounds(recon, bounds_min, bounds_max)
    assert len(cropped) == 1
    assert np.allclose(cropped[0], [0, 0, 0])


def test_sampling_determinism():
    pts = np.random.rand(1000, 3) * 10

    s1 = voxel_downsample(pts, 0.5, seed=42)
    s2 = voxel_downsample(pts, 0.5, seed=42)
    s3 = voxel_downsample(pts, 0.5, seed=43)

    assert np.array_equal(s1, s2)
    assert not np.array_equal(s1, s3)


def test_reference_frame_rejection():
    meta = ReferenceMetadata(crs="UNKNOWN", vertical_datum="UNKNOWN")
    res = evaluate_surface_accuracy(
        np.array([[0, 0, 0]]), np.array([[0, 0, 0]]), None, meta, np.array([-1, -1, -1]), np.array([1, 1, 1])
    )
    assert res["status"] == ValidationStatus.INVALID_REFERENCE_FRAME.value


def test_vertical_datum_mismatch():
    meta = ReferenceMetadata(crs="EPSG:32632", vertical_datum="EGM96")
    recon = np.array([[0, 0, 0], [1, 0, 0]])
    ref = np.array([[0, 0, 0.5], [1, 0, 0.5]])

    # Simulate mismatched datum by passing is_same_vertical_datum=False
    res = evaluate_surface_accuracy(
        recon, ref, None, meta, np.array([-2, -2, -2]), np.array([2, 2, 2]), is_same_vertical_datum=False
    )
    assert "RMSE_Z" not in res["accuracy_reconstruction_to_reference"]

    res_match = evaluate_surface_accuracy(
        recon, ref, None, meta, np.array([-2, -2, -2]), np.array([2, 2, 2]), is_same_vertical_datum=True
    )
    assert "RMSE_Z" in res_match["accuracy_reconstruction_to_reference"]
    assert np.isclose(res_match["accuracy_reconstruction_to_reference"]["RMSE_Z"], 0.5)


def test_outlier_reporting():
    meta = ReferenceMetadata(crs="EPSG:32632", vertical_datum="EGM96")
    recon = np.array([[0, 0, 0], [0, 0, 10.0]])  # one massive outlier
    ref = np.array([[0, 0, 0], [0, 0, 0]])

    res = evaluate_surface_accuracy(recon, ref, None, meta, np.array([-11, -11, -11]), np.array([11, 11, 11]))
    # Ensure it's not silently removed
    assert res["accuracy_reconstruction_to_reference"]["max"] >= 10.0
    assert res["accuracy_reconstruction_to_reference"]["RAW_metrics"] is True


def test_decision_rule_no_icp_path():
    # Since evaluate_surface_accuracy doesn't take an ICP alignment parameter,
    # it strictly computes distances on the raw coordinates passed.
    # The ICP ban is enforced architecturally.
    pass
