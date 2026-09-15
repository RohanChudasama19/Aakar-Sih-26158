import numpy as np
import pytest

from app.camera import CameraModel, CameraModelType, Undistorter


def test_valid_camera_model():
    cam = CameraModel(
        model_type=CameraModelType.PINHOLE,
        width=1920,
        height=1080,
        fx=1000.0,
        fy=1000.0,
        cx=960.0,
        cy=540.0,
    )
    assert cam.original_width == 1920
    assert cam.to_matrix()[0, 0] == 1000.0


def test_invalid_focal_length():
    with pytest.raises(ValueError):
        CameraModel.from_dict({"image_width": 100, "image_height": 100, "fx": -5.0})


def test_malformed_distortion():
    cam = CameraModel.from_dict({"image_width": 100, "image_height": 100, "fx": 100.0, "distortion": "invalid"})
    assert cam.distortion == []


def test_scaling_intrinsics():
    cam = CameraModel(
        model_type=CameraModelType.PINHOLE,
        width=3840,
        height=2160,
        fx=2000.0,
        fy=2000.0,
        cx=1920.0,
        cy=1080.0,
    )
    scaled = cam.scale(1920, 1080)
    assert scaled.fx == 1000.0
    assert scaled.fy == 1000.0
    assert scaled.cx == 960.0
    assert scaled.cy == 540.0
    assert scaled.width == 1920
    assert scaled.height == 1080
    assert scaled.original_width == 3840


def test_non_uniform_scaling():
    cam = CameraModel(
        model_type=CameraModelType.PINHOLE,
        width=1000,
        height=1000,
        fx=500.0,
        fy=500.0,
        cx=500.0,
        cy=500.0,
    )
    scaled = cam.scale(500, 250)
    assert scaled.fx == 250.0
    assert scaled.fy == 125.0
    assert scaled.cx == 250.0
    assert scaled.cy == 125.0


def test_crop_transformation():
    cam = CameraModel(
        model_type=CameraModelType.PINHOLE,
        width=1000,
        height=1000,
        fx=500.0,
        fy=500.0,
        cx=500.0,
        cy=500.0,
    )
    cropped = cam.crop(100.0, 50.0, 800, 900)
    assert cropped.cx == 400.0
    assert cropped.cy == 450.0
    assert cropped.fx == 500.0


def test_opencv_matrix_conversion():
    cam = CameraModel(model_type=CameraModelType.PINHOLE, width=100, height=100, fx=10, fy=11, cx=12, cy=13, skew=1.0)
    mat = cam.to_matrix()
    assert mat[0, 0] == 10
    assert mat[1, 1] == 11
    assert mat[0, 2] == 12
    assert mat[1, 2] == 13
    assert mat[0, 1] == 1.0


def test_colmap_conversion():
    cam = CameraModel(
        model_type=CameraModelType.SIMPLE_RADIAL, width=100, height=100, fx=10, fy=10, cx=12, cy=13, distortion=[0.1]
    )
    assert cam.to_colmap() == "10,12,13,0.1"


def test_distortion_undistortion_zero():
    cam = CameraModel(model_type=CameraModelType.PINHOLE, width=100, height=100, fx=50, fy=50, cx=50, cy=50)
    ud = Undistorter(cam)
    img = np.ones((100, 100, 3), dtype=np.uint8)
    out = ud.undistort_image(img)
    assert out.shape == (100, 100, 3)
    assert ud.get_undistorted_camera().fx == 50


def test_round_trip_undistortion():
    cam = CameraModel(
        model_type=CameraModelType.RADIAL, width=100, height=100, fx=50, fy=50, cx=50, cy=50, distortion=[0.1, 0.05]
    )
    ud = Undistorter(cam)
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[50, 50] = [255, 255, 255]
    out = ud.undistort_image(img)
    assert out.shape == (100, 100, 3)
    # The center pixel shouldn't move under pure radial distortion
    assert out[50, 50, 0] > 0
