import numpy as np

from app.pipeline.surface import reconstruct_surface


def test_poisson_hallucination_trimming():
    """
    Test that Poisson doesn't hallucinate large enclosing bubbles around thin planar surfaces,
    or if it does, that the density trimming strictly removes them.
    """
    # Create a dense flat plane of points
    y, z = np.meshgrid(np.linspace(-1, 1, 30), np.linspace(-1, 1, 30))
    points = np.c_[np.zeros(y.size), y.ravel(), z.ravel()]
    colors = np.full((len(points), 3), 150, np.uint8)

    # Place a single camera observing it head-on
    cameras = np.array([[5.0, 0, 0]])

    # Reconstruct surface
    mesh, report = reconstruct_surface(points, colors, cameras, options={"density_quantile": 0.05})

    # Since it's a flat open plane, Poisson naturally tries to close it into a bubble
    # We expect our trimming to delete the back side of the bubble because it has NO support
    # (distance to closest point is large, density is low)

    # Check that no vertex is far behind the plane (x < -0.2)
    min_x = np.min(mesh.vertices[:, 0])

    # If trimming failed, it would create a large back-bubble at x < -1.0 or more
    assert min_x > -0.5, f"Poisson hallucinated unsupported geometry at x={min_x}"

    # Verify the unobserved ratio reflects that we don't have large unobserved areas
    # If the bubble remained, unobserved ratio would be very high
    assert report.get("unobserved_face_ratio", 0) < 0.2
