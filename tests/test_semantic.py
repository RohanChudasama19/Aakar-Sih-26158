import numpy as np
import pytest
import trimesh

from app.pipeline.semantic import (
    CLASS_TO_ID,
    ModelSemanticBackend,
    classify,
)


def test_heuristic_fallback_triggers():
    # ModelSemanticBackend should raise error since we don't have a model
    backend = ModelSemanticBackend()
    with pytest.raises(RuntimeError, match="No licensed model weights"):
        backend.classify(None, None, None, None, None, None, None, None)

    # The main classify function should catch this and fallback
    # We will test it with synthetic data
    points = np.array([[0, 0, 0], [0, 0, 10]])
    colors = np.array([[100, 100, 100], [0, 255, 0]], dtype=np.uint8)
    geo = {
        "metric_state": "GEOREFERENCED",
        "valid": True,
        "translation": np.zeros(3),
        "rotation": np.eye(3),
        "scale": 1.0,
    }

    mesh = trimesh.Trimesh(
        vertices=np.array([[-1, -1, 0], [1, -1, 0], [0, 1, 0], [-1, -1, 10], [1, -1, 10], [0, 1, 10]]),
        faces=np.array([[0, 1, 2], [3, 4, 5]]),
    )

    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        report = classify(points, colors, geo, mesh, out)

        # Verify it fell back
        assert report["semantic_backend"] == "HEURISTIC_FALLBACK"
        assert report["semantic_status"] == "SEMANTICS_DEGRADED"
        assert "HEURISTIC" in report["semantic_backend"]

        # The first face (Z=0, gray) should be ROAD, the second face (Z=10, green) should be VEGETATION.
        assert report["classes"]["VEGETATION"]["face_count"] == 1
        assert report["classes"]["ROAD"]["face_count"] == 1


def test_unknown_class():
    points = np.array([[0, 0, 0]])
    colors = np.array([[0, 0, 0]], dtype=np.uint8)  # Dark
    geo = {"metric_state": "RELATIVE", "valid": False}
    mesh = trimesh.Trimesh(vertices=np.array([[-1, -1, 0], [1, -1, 0], [0, 1, 0]]), faces=np.array([[0, 1, 2]]))

    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        report = classify(points, colors, geo, mesh, out, options={"force_heuristic": True})

        # Relative metric state fallback puts ground, but vegetation overrides it.
        # Wait, the fallback in relative is GROUND. Let's see if the point has UNKNOWN.
        labels_path = out / "semantic_labels.npz"
        with np.load(labels_path) as data:
            assert data["face_labels"][0] == CLASS_TO_ID["UNKNOWN"]

        assert "UNKNOWN" in report["classes"]
        assert report["classes"]["UNKNOWN"]["face_count"] == 1


def test_dynamic_masking_separation():
    # Just ensuring dynamic logic isn't baked into the core static classes
    assert "PERSON" not in CLASS_TO_ID
    assert "VEHICLE" not in CLASS_TO_ID  # Vehicle is a subclass, not a main class.
