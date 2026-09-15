import numpy as np

from app.pipeline.readiness import CONFIG, analyze_telemetry, compute_exposure, compute_features


def test_compute_exposure():
    # Dark image
    dark = np.zeros((100, 100), dtype=np.uint8)
    res_dark = compute_exposure(dark, CONFIG["exposure"])
    assert res_dark["is_dark"]
    assert not res_dark["is_overexposed"]

    # Bright image
    bright = np.full((100, 100), 255, dtype=np.uint8)
    res_bright = compute_exposure(bright, CONFIG["exposure"])
    assert not res_bright["is_dark"]
    assert res_bright["is_overexposed"]

    # Normal image
    normal = np.random.randint(50, 200, (100, 100), dtype=np.uint8)
    res_normal = compute_exposure(normal, CONFIG["exposure"])
    assert not res_normal["is_dark"]
    assert not res_normal["is_overexposed"]


def test_compute_features_concentrated():
    # Create image with features only in one corner
    img = np.zeros((400, 400), dtype=np.uint8)
    # Add noise to top-left corner to create features
    img[0:50, 0:50] = np.random.randint(0, 255, (50, 50), dtype=np.uint8)

    _, _, res = compute_features(img, CONFIG["features"])
    assert res["is_concentrated"]
    assert res["occupancy_ratio"] < 0.3


def test_compute_features_distributed():
    # Create image with noise everywhere
    img = np.random.randint(0, 255, (400, 400), dtype=np.uint8)

    _, _, res = compute_features(img, CONFIG["features"])
    assert not res["is_concentrated"]


def test_analyze_telemetry():
    # Missing telemetry
    res_missing = analyze_telemetry([], {}, CONFIG["telemetry"])
    assert "Missing mandatory GPS telemetry." in res_missing["blocking_reasons"]

    # Valid telemetry
    valid_gps = [
        {"time": 0.0, "latitude": 0.0, "longitude": 0.0, "frame": 0},
        {"time": 1.0, "latitude": 0.0001, "longitude": 0.0, "frame": 30},
        {"time": 2.0, "latitude": 0.0002, "longitude": 0.0, "frame": 60},
    ]
    res_valid = analyze_telemetry(valid_gps, {}, CONFIG["telemetry"])
    assert not res_valid["blocking_reasons"]
    assert not res_valid["warnings"]

    # Gaps
    gap_gps = [
        {"time": 0.0, "latitude": 0.0, "longitude": 0.0, "frame": 0},
        {"time": 5.0, "latitude": 0.0001, "longitude": 0.0, "frame": 150},
    ]
    res_gap = analyze_telemetry(gap_gps, {}, CONFIG["telemetry"])
    assert any("gap" in w for w in res_gap["warnings"])


def test_readiness_pipeline_unreadable(tmp_path):
    from app.pipeline.readiness import perform_analysis

    res = perform_analysis(tmp_path / "missing.mp4", [], {}, None)
    assert res["status"] == "NOT_READY"
    assert "Cannot decode" in str(res["blocking_reasons"])
