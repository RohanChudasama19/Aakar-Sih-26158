import numpy as np
import pytest; torch = pytest.importorskip("torch")

from app.pipeline.semantic_model import UAVID_TO_AAKAR, AAKARClass, SemanticPipeline, UAVidClass
from scripts.semantic.train import build_model, compute_iou, rgb_to_mask


def test_class_mapping():
    assert UAVID_TO_AAKAR[UAVidClass.BUILDING] == AAKARClass.BUILDING
    assert UAVID_TO_AAKAR[UAVidClass.ROAD] == AAKARClass.ROAD
    assert UAVID_TO_AAKAR[UAVidClass.TREE] == AAKARClass.VEGETATION
    assert UAVID_TO_AAKAR[UAVidClass.LOW_VEGETATION] == AAKARClass.VEGETATION
    assert UAVID_TO_AAKAR[UAVidClass.STATIC_CAR] == AAKARClass.OBSTACLE
    assert UAVID_TO_AAKAR[UAVidClass.MOVING_CAR] == AAKARClass.DYNAMIC_OBJECT
    assert UAVID_TO_AAKAR[UAVidClass.HUMAN] == AAKARClass.DYNAMIC_OBJECT
    assert UAVID_TO_AAKAR[UAVidClass.CLUTTER] == AAKARClass.UNKNOWN


def test_semantic_pipeline_fallback():
    # Model doesn't exist, should fallback to heuristics
    pipeline = SemanticPipeline()
    assert pipeline.state.value == "HEURISTIC_FALLBACK"

    img = np.zeros((100, 100, 3), dtype=np.uint8)
    class_mask, conf_map, dyn_mask = pipeline.infer_image(img)

    assert class_mask.shape == (100, 100)
    assert conf_map.shape == (100, 100)
    assert dyn_mask.shape == (100, 100)
    assert np.all(class_mask == UAVidClass.CLUTTER.value)
    assert np.all(conf_map == 0.0)


def test_2d_to_3d_projection():
    pipeline = SemanticPipeline()

    points_3d = np.array(
        [
            [0.0, 0.0, 5.0],
            [1.0, 1.0, -1.0],  # Behind camera
            [100.0, 100.0, 5.0],  # Out of bounds
        ]
    )

    camera_pose = np.eye(4)  # Camera at origin
    intrinsics = np.array([[500.0, 0.0, 50.0], [0.0, 500.0, 50.0], [0.0, 0.0, 1.0]])

    class_mask = np.full((100, 100), UAVidClass.BUILDING.value, dtype=np.uint8)
    conf_map = np.ones((100, 100), dtype=np.float32)

    classes, confs = pipeline.project_2d_to_3d(points_3d, camera_pose, intrinsics, class_mask, conf_map)

    assert len(classes) == 3
    assert classes[0] == UAVidClass.BUILDING.value
    assert confs[0] == 1.0

    assert classes[1] == UAVidClass.CLUTTER.value
    assert confs[1] == 0.0

    assert classes[2] == UAVidClass.CLUTTER.value
    assert confs[2] == 0.0


def test_multi_view_fusion():
    pipeline = SemanticPipeline()

    c_obs1 = np.array([UAVidClass.BUILDING.value, UAVidClass.ROAD.value, UAVidClass.CLUTTER.value])
    conf_obs1 = np.array([0.9, 0.4, 0.0])

    c_obs2 = np.array([UAVidClass.BUILDING.value, UAVidClass.TREE.value, UAVidClass.CLUTTER.value])
    conf_obs2 = np.array([0.8, 0.6, 0.0])

    fused_c, fused_conf, support = pipeline.fuse_multi_view([c_obs1, c_obs2], [conf_obs1, conf_obs2])

    assert fused_c[0] == UAVidClass.BUILDING.value
    assert fused_conf[0] > 0.8
    assert support[0] == 2

    assert fused_c[1] == UAVidClass.TREE.value
    assert support[1] == 2

    assert fused_c[2] == UAVidClass.CLUTTER.value
    assert support[2] == 0


def test_temporal_confirmation():
    pipeline = SemanticPipeline()
    m1 = np.array([True, False, False])
    m2 = np.array([False, True, False])
    out = pipeline.temporally_confirm_dynamics([m1, m2])
    assert np.array_equal(out, np.array([True, True, False]))


import pytest


def test_rgb_class_conversion():
    # Valid RGB to int map
    test_img = np.zeros((10, 10, 3), dtype=np.uint8)
    test_img[0, 0] = [128, 0, 0]  # Building -> 1
    test_img[1, 1] = [192, 0, 192]  # Static Car -> 6
    test_img[2, 2] = [0, 0, 0]  # Clutter -> 0

    mask = rgb_to_mask(test_img)
    assert mask[0, 0] == 1
    assert mask[1, 1] == 6
    assert mask[2, 2] == 0
    assert mask[3, 3] == 0  # Default zeros are Clutter (0,0,0)


def test_unknown_color_detection():
    test_img = np.zeros((10, 10, 3), dtype=np.uint8)
    test_img[0, 0] = [1, 2, 3]  # Unknown!

    with pytest.raises(ValueError, match="Unknown colors found"):
        rgb_to_mask(test_img)


def test_nearest_neighbor_mask_resize():
    # Nearest neighbor interpolation test
    import cv2

    mask = np.array([[1, 2], [3, 4]], dtype=np.uint8)
    resized = cv2.resize(mask, (4, 4), interpolation=cv2.INTER_NEAREST)

    # Must only contain original values
    unique_vals = set(np.unique(resized))
    assert unique_vals.issubset({1, 2, 3, 4})
    assert 1 in unique_vals


def test_model_8_class_output():
    # Build model, check channels
    model, weights = build_model(num_classes=8)
    dummy_input = torch.randn(1, 3, 64, 64)
    model.eval()
    with torch.no_grad():
        out = model(dummy_input)["out"]

    assert out.shape == (1, 8, 64, 64)
    assert out.dtype == torch.float32


def test_confusion_matrix_metrics():
    # Perfect matrix
    conf = np.eye(8, dtype=np.int64) * 10
    iou, p, r, f1 = compute_iou(conf)
    assert np.allclose(iou, 1.0)
    assert np.allclose(p, 1.0)
    assert np.allclose(r, 1.0)

    # Mixed matrix
    conf2 = np.zeros((8, 8), dtype=np.int64)
    conf2[1, 1] = 5  # True Building
    conf2[2, 1] = 5  # Predicted Road, True Building

    iou2, p2, r2, f12 = compute_iou(conf2)
    assert iou2[1] == 0.5
    assert iou2[2] == 0.0


def test_checkpoint_resume(tmp_path):
    model, _ = build_model(num_classes=8)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    ckpt_path = tmp_path / "test_ckpt.pth"

    # Save
    torch.save(
        {"epoch": 5, "model_state": model.state_dict(), "optimizer_state": opt.state_dict(), "miou": 0.45}, ckpt_path
    )

    # Load
    checkpoint = torch.load(ckpt_path)
    model.load_state_dict(checkpoint["model_state"])
    opt.load_state_dict(checkpoint["optimizer_state"])

    assert checkpoint["epoch"] == 5
    assert checkpoint["miou"] == 0.45
