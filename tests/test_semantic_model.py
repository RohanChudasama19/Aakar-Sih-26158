import numpy as np

from app.pipeline.semantic import CLASS_TO_ID, classify
from app.pipeline.semantic_model import SemanticModelBackend, get_backend_status


def test_class_mapping():
    assert CLASS_TO_ID["UNKNOWN"] == 0
    assert CLASS_TO_ID["SEMANTIC_DYNAMIC_CANDIDATE"] == 8
    assert CLASS_TO_ID["TEMPORALLY_CONFIRMED_DYNAMIC"] == 9


def test_fallback_on_missing_model(tmp_path):
    status = get_backend_status(str(tmp_path / "nonexistent.onnx"))
    assert status == "HEURISTIC_FALLBACK"


def test_fallback_prevents_fake_ai_claim(tmp_path):
    pts = np.random.rand(10, 3)
    colors = np.random.rand(10, 3)

    class DummyMesh:
        vertices = np.random.rand(10, 3)
        faces = np.array([[0, 1, 2], [3, 4, 5]])
        triangles_center = np.random.rand(2, 3)
        face_normals = np.random.rand(2, 3)
        area_faces = np.ones(2)

        def copy(self):
            return self

        def export(self, path):
            pass

        visual = type("Vis", (), {"face_colors": None})

    mesh = DummyMesh()

    report = classify(pts, colors, {"metric_state": "RELATIVE"}, mesh, tmp_path, options={"force_heuristic": True})

    assert report["semantic_backend"] == "HEURISTIC_FALLBACK"
    assert report["semantic_status"] == "SEMANTICS_DEGRADED"


def test_dynamic_candidate_logic(tmp_path):
    pts = np.random.rand(10, 3)
    colors = np.random.rand(10, 3)

    class DummyMesh:
        vertices = np.random.rand(10, 3)
        faces = np.array(
            [
                [0, 1, 2],
                [3, 4, 5],
                [1, 2, 3],
                [4, 5, 6],
                [2, 3, 4],
                [5, 6, 7],
                [3, 4, 5],
                [6, 7, 8],
                [4, 5, 6],
                [7, 8, 9],
            ]
        )
        triangles_center = np.random.rand(10, 3)
        face_normals = np.random.rand(10, 3)
        area_faces = np.ones(10)

        def copy(self):
            return self

        def export(self, path):
            pass

        visual = type("Vis", (), {"face_colors": None})

    mesh = DummyMesh()

    report = classify(
        pts,
        colors,
        {"metric_state": "RELATIVE"},
        mesh,
        tmp_path,
        options={"model_path": "models/semantic/model.onnx", "test_dynamic": True, "temporal_confirm": True},
    )

    # We masked 5 dynamic objects in ModelSemanticBackend mock
    assert report["dynamic_objects_masked"] == 5


def test_semantic_model_backend():
    model = SemanticModelBackend("dummy_path")
    assert model.status == "MODEL_UNAVAILABLE"

    out = model.infer_frame(np.zeros((512, 512, 3), dtype=np.uint8))
    assert out["status"] == "MODEL_UNAVAILABLE"
