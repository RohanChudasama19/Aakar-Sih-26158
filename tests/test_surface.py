import numpy as np

from app.pipeline.surface import reconstruct_surface


def test_vertical_facade_preserved_in_three_dimensions():
    # An XY-projected mesher collapses this entire wall to a line.
    y, z = np.meshgrid(np.linspace(-2, 2, 65), np.linspace(0, 3, 50))
    points = np.c_[np.zeros(y.size), y.ravel(), z.ravel()]
    colors = np.full((len(points), 3), 170, np.uint8)
    mesh, report = reconstruct_surface(points, colors, np.array([[5.0, 0, 1.5]]))
    assert len(mesh.faces) > 500
    assert np.ptp(mesh.vertices[:, 1]) > 3.5
    assert np.ptp(mesh.vertices[:, 2]) > 2.5
    assert np.quantile(abs(mesh.vertices[:, 0]), 0.95) < 0.1
    assert report["largest_component_fraction"] > 0.9
    assert report["method"].startswith("3D_")
