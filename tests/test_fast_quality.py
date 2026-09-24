import pytest
from app.pipeline.profiles import FAST_QUALITY_V1
from app.pipeline.sfm_backend import determine_profile as sfm_det
from app.pipeline.dense_backend import determine_dense_profile as dense_det

def test_fast_quality_profile_resolution():
    options = {"profile": "FAST_QUALITY"}
    
    # 1. SFM Profile
    sfm_prof = sfm_det({}, None, options)
    assert sfm_prof.name == "FAST_QUALITY"
    assert sfm_prof.max_frames == FAST_QUALITY_V1["sfm_budget"]
    assert sfm_prof.matching_overlap == FAST_QUALITY_V1["matching_settings"]["overlap"]
    assert sfm_prof.mapper_strategy == "GLOBAL_FAST"
    
    # 2. Dense Profile
    dense_prof = dense_det(0, options)
    assert dense_prof["name"] == "FAST_QUALITY"
    assert dense_prof["reference_target"] == FAST_QUALITY_V1["dense_settings"]["reference_target"]
    assert dense_prof["window_step"] == FAST_QUALITY_V1["dense_settings"]["window_step"]
    assert dense_prof["num_iterations"] == FAST_QUALITY_V1["dense_settings"]["num_iterations"]
    assert dense_prof["min_num_pixels"] == FAST_QUALITY_V1["fusion_settings"]["min_num_pixels"]

def test_centralized_profile_config():
    assert FAST_QUALITY_V1["candidate_budget"] == 400
    assert FAST_QUALITY_V1["sfm_budget"] == 250
    assert FAST_QUALITY_V1["sift_settings"]["max_num_features"] == 4096
    assert FAST_QUALITY_V1["dense_settings"]["reference_target"] == 105
    assert FAST_QUALITY_V1["dense_settings"]["max_image_size"] == 1600
    assert FAST_QUALITY_V1["dense_settings"]["geom_consistency"] is True
