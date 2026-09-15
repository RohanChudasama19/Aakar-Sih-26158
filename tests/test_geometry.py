import cv2
import numpy as np

from app.pipeline.georef import similarity
from app.pipeline.sfm import triangulate
from app.schemas import intrinsics


def test_similarity_recovers_known_metric_transform():
    rng = np.random.default_rng(7)
    a = rng.normal(size=(30, 3))
    r = cv2.Rodrigues(np.array([0.3, -0.2, 0.1]))[0]
    b = 4.2 * a @ r.T + np.array([20, 35, 4])
    scale, rotation, t = similarity(a, b)
    assert abs(scale - 4.2) < 1e-10
    np.testing.assert_allclose(scale * a @ rotation.T + t, b, atol=1e-10)


def test_triangulation_rejects_negative_depth_and_recovers_visible_points():
    k = np.array([[500.0, 0, 320], [0, 500, 240], [0, 0, 1]])
    a = np.c_[np.eye(3), np.zeros(3)]
    b = np.c_[np.eye(3), np.array([-1.0, 0, 0])]
    points = np.array([[0.0, 0, 5], [1.0, 1, 6], [0.0, 1, -4]])

    def project(p):
        c = points @ p[:, :3].T + p[:, 3]
        v = c @ k.T
        return v[:, :2] / v[:, 2:3]

    got, good = triangulate(k, a, b, project(a), project(b))
    assert good.tolist() == [True, True, False]
    np.testing.assert_allclose(got[:2], points[:2], atol=1e-8)


def test_intrinsics_preserve_pixel_scale():
    m = {"camera_intrinsics": {"focal_length_mm": 5.5, "sensor_width_mm": 6.4, "sensor_height_mm": 4.8}}
    k = intrinsics(m, 640, 480)
    np.testing.assert_allclose(k.to_matrix(), [[550, 0, 320], [0, 550, 240], [0, 0, 1]])


def test_collinear_gps_does_not_claim_absolute_orientation(tmp_path):
    from app.pipeline.georef import align

    poses = {i: np.c_[np.eye(3), [-float(i), 0, 0]] for i in range(4)}
    info = {"frames": [{"frame": i, "time_sec": float(i)} for i in range(4)], "start_time_utc": 0.0}
    gps = [
        {"frame": i, "time": float(i), "latitude": 23.0, "longitude": 72.0 + i * 0.00001, "altitude_m": 50.0}
        for i in range(4)
    ]
    result = align({"poses": poses}, info, gps, tmp_path)
    assert not result["valid"] and result["rmse_m"] is None
