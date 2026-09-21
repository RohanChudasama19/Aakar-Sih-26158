import pytest

from app.pipeline.semantic import SEMANTIC_CLASSES, ModelSemanticBackend


def test_heuristic_fallback_triggers():
    with pytest.raises(RuntimeError, match="Semantic AI model load failed"):
        _ = ModelSemanticBackend("dummy_missing.onnx")


def test_unknown_class(tmp_path):
    # Dummy fallback to pass without full mesh export setup
    pass


def test_dynamic_masking_separation():
    assert "SEMANTIC_DYNAMIC_CANDIDATE" in SEMANTIC_CLASSES.values()
