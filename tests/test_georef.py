import numpy as np

from app.pipeline.georef import similarity


def test_similarity_exact():
    # Synthesize geometry
    np.random.seed(42)
    a = np.random.randn(10, 3)

    # Scale, Rotate, Translate
    s = 2.5
    theta = np.radians(30)
    r = np.array([[np.cos(theta), -np.sin(theta), 0], [np.sin(theta), np.cos(theta), 0], [0, 0, 1]])
    t = np.array([10.0, -5.0, 2.0])

    b = s * a @ r.T + t

    s_est, r_est, t_est = similarity(a, b)

    assert np.isclose(s, s_est)
    assert np.allclose(r, r_est)
    assert np.allclose(t, t_est)


def test_similarity_degenerate():
    a = np.zeros((10, 3))
    b = np.zeros((10, 3))

    s, r, t = similarity(a, b)
    assert s == 1.0


def test_transform_applies_full_sim3():
    from app.pipeline.georef import transform

    np.random.seed(42)
    points = np.random.randn(50, 3)

    geo = {
        "metric_state": "GEOREFERENCED_METRIC",
        "scale": 3.14,
        "rotation": [[0, -1, 0], [1, 0, 0], [0, 0, 1]],
        "translation": [100.0, 200.0, 50.0],
    }

    transformed = transform(points, geo)

    # Manual application: X_world = s * R * X_relative + t (or s * X @ R.T + t)
    s = geo["scale"]
    r = np.array(geo["rotation"])
    t = np.array(geo["translation"])
    expected = s * points @ r.T + t

    assert np.allclose(transformed, expected)
    # Ensure it's not just translation
    assert not np.allclose(transformed, points + t)
