import pytest
import numpy as np
from app.pipeline.semantic_model import SemanticPipeline, UAVidClass, AeroReconClass, UAVID_TO_AERORECON

def test_class_mapping():
    assert UAVID_TO_AERORECON[UAVidClass.BUILDING] == AeroReconClass.BUILDING
    assert UAVID_TO_AERORECON[UAVidClass.ROAD] == AeroReconClass.ROAD
    assert UAVID_TO_AERORECON[UAVidClass.TREE] == AeroReconClass.VEGETATION
    assert UAVID_TO_AERORECON[UAVidClass.LOW_VEGETATION] == AeroReconClass.VEGETATION
    assert UAVID_TO_AERORECON[UAVidClass.STATIC_CAR] == AeroReconClass.OBSTACLE
    assert UAVID_TO_AERORECON[UAVidClass.MOVING_CAR] == AeroReconClass.DYNAMIC_OBJECT
    assert UAVID_TO_AERORECON[UAVidClass.HUMAN] == AeroReconClass.DYNAMIC_OBJECT
    assert UAVID_TO_AERORECON[UAVidClass.CLUTTER] == AeroReconClass.UNKNOWN

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
    
    points_3d = np.array([
        [0.0, 0.0, 5.0],
        [1.0, 1.0, -1.0],  # Behind camera
        [100.0, 100.0, 5.0] # Out of bounds
    ])
    
    camera_pose = np.eye(4) # Camera at origin
    intrinsics = np.array([
        [500.0, 0.0, 50.0],
        [0.0, 500.0, 50.0],
        [0.0, 0.0, 1.0]
    ])
    
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
    
    fused_c, fused_conf, support = pipeline.fuse_multi_view(
        [c_obs1, c_obs2],
        [conf_obs1, conf_obs2]
    )
    
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

