from app.pipeline.sfm_backend import determine_profile


def test_determine_profile_small():
    info = {"frames": [{"name": str(i)} for i in range(150)]}
    profile = determine_profile(info)
    assert profile.name == "SMALL"
    assert profile.mapper_strategy == "INCREMENTAL"
    assert profile.matching_overlap == 8


def test_determine_profile_medium():
    info = {"frames": [{"name": str(i)} for i in range(500)]}
    profile = determine_profile(info)
    assert profile.name == "MEDIUM"
    assert profile.mapper_strategy == "INCREMENTAL"
    assert profile.matching_overlap == 15


def test_determine_profile_large():
    info = {"frames": [{"name": str(i)} for i in range(1200)]}
    profile = determine_profile(info)
    assert profile.name == "LARGE"
    assert profile.mapper_strategy == "GLOBAL"
    assert profile.matching_overlap == 25


def test_determine_profile_very_large():
    info = {"frames": [{"name": str(i)} for i in range(3000)]}
    profile = determine_profile(info)
    assert profile.name == "VERY_LARGE"
    assert profile.mapper_strategy == "HIERARCHICAL"
