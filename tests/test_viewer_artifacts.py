"""
Tests for viewer artifact generation (sparse PLY, dense display cloud,
confidence mesh, semantic copy, cameras.json).

All tests use synthetic data; no reconstruction is run.
"""

import numpy as np
import trimesh

from app.pipeline.viewer_artifacts import (
    generate_all_viewer_artifacts,
    generate_cameras_json,
    generate_confidence_mesh_ply,
    generate_dense_display_ply,
    generate_semantic_viewer_artifacts,
    generate_sparse_ply,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _random_pts(n: int, seed: int = 42) -> tuple:
    rng = np.random.default_rng(seed)
    pts = rng.random((n, 3)).astype(np.float32)
    cols = (rng.random((n, 3)) * 255).astype(np.uint8)
    return pts, cols


def _make_simple_mesh() -> trimesh.Trimesh:
    """A minimal valid trimesh with support metadata."""
    verts = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]], dtype=float)
    faces = np.array([[0, 1, 2], [1, 3, 2]])
    m = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    m.metadata["supported_face_ratio"] = 0.5
    m.metadata["weak_face_ratio"] = 0.3
    m.metadata["unobserved_face_ratio"] = 0.2
    return m


def _fake_poses(n: int = 5) -> dict:
    rng = np.random.default_rng(0)
    poses = {}
    for i in range(n):
        R = np.eye(3)
        t = rng.random(3)
        poses[str(i)] = np.hstack([R, t[:, None]]).tolist()
    return poses


# ── Import under test marker (imports are at top) ─────────────────────────────

# ── Sparse PLY ────────────────────────────────────────────────────────────────


def test_sparse_ply_creates_file(tmp_path):
    pts, cols = _random_pts(200)
    result = generate_sparse_ply(pts, cols, tmp_path)
    assert result["available"] is True
    assert (tmp_path / "sparse" / "sparse.ply").is_file()
    assert (tmp_path / "sparse" / "sparse.ply").stat().st_size > 0


def test_sparse_ply_point_count(tmp_path):
    pts, cols = _random_pts(150)
    result = generate_sparse_ply(pts, cols, tmp_path)
    assert result["point_count"] == 150


def test_sparse_ply_empty_returns_unavailable(tmp_path):
    result = generate_sparse_ply(np.empty((0, 3)), np.empty((0, 3)), tmp_path)
    assert result["available"] is False


# ── Dense display cloud ───────────────────────────────────────────────────────


def test_dense_display_ply_creates_file(tmp_path):
    pts, cols = _random_pts(500)
    result = generate_dense_display_ply(pts, cols, tmp_path)
    assert result["available"] is True
    ply = tmp_path / "pointcloud" / "dense_display.ply"
    assert ply.is_file() and ply.stat().st_size > 0


def test_dense_display_no_downsample_under_budget(tmp_path):
    """If original count ≤ max, display count == original count."""
    pts, cols = _random_pts(100)
    result = generate_dense_display_ply(pts, cols, tmp_path, max_points=200)
    assert result["display_point_count"] == 100
    assert result["downsampling_method"] == "none"


def test_dense_display_downsample_over_budget(tmp_path):
    """If original count > max, display count ≤ max."""
    pts, cols = _random_pts(5000)
    result = generate_dense_display_ply(pts, cols, tmp_path, max_points=500)
    assert result["display_point_count"] <= 500
    assert result["original_point_count"] == 5000
    assert result["downsampling_method"] != "none"


def test_dense_display_preserves_analysis_cloud(tmp_path):
    """Canonical dense_filtered.ply must NOT be touched."""
    # Create a fake analysis cloud
    analysis = tmp_path / "dense_filtered.ply"
    analysis.write_bytes(b"FAKE_PLY_CONTENT")
    pts, cols = _random_pts(100)
    generate_dense_display_ply(pts, cols, tmp_path)
    # Analysis cloud unchanged
    assert analysis.read_bytes() == b"FAKE_PLY_CONTENT"


def test_dense_display_deterministic(tmp_path, tmp_path_factory):
    """Two calls with identical inputs must produce identical point counts."""
    pts, cols = _random_pts(5000)
    r1 = generate_dense_display_ply(pts, cols, tmp_path_factory.mktemp("a"), max_points=300)
    r2 = generate_dense_display_ply(pts, cols, tmp_path_factory.mktemp("b"), max_points=300)
    assert r1["display_point_count"] == r2["display_point_count"]


# ── Confidence mesh ───────────────────────────────────────────────────────────


def test_confidence_mesh_creates_file(tmp_path):
    mesh = _make_simple_mesh()
    result = generate_confidence_mesh_ply(mesh, tmp_path)
    assert result["available"] is True
    ply = tmp_path / "mesh" / "confidence_mesh.ply"
    assert ply.is_file() and ply.stat().st_size > 0


def test_confidence_mesh_creates_summary(tmp_path):
    mesh = _make_simple_mesh()
    generate_confidence_mesh_ply(mesh, tmp_path)
    summary = tmp_path / "mesh" / "surface_support_summary.json"
    assert summary.is_file()
    import json

    data = json.loads(summary.read_text())
    assert "supported_face_ratio" in data
    assert "weak_face_ratio" in data
    assert "unobserved_face_ratio" in data
    assert "note" in data


def test_confidence_mesh_ratios_recorded(tmp_path):
    mesh = _make_simple_mesh()
    result = generate_confidence_mesh_ply(mesh, tmp_path)
    assert abs(result["supported_face_ratio"] - 0.5) < 1e-6
    assert abs(result["weak_face_ratio"] - 0.3) < 1e-6


def test_confidence_mesh_none_returns_unavailable(tmp_path):
    result = generate_confidence_mesh_ply(None, tmp_path)
    assert result["available"] is False


# ── Cameras JSON ──────────────────────────────────────────────────────────────


def test_cameras_json_creates_file(tmp_path):
    poses = _fake_poses(6)
    result = generate_cameras_json(poses, tmp_path)
    assert result["available"] is True
    cj = tmp_path / "sparse" / "cameras.json"
    assert cj.is_file()


def test_cameras_json_count(tmp_path):
    poses = _fake_poses(4)
    result = generate_cameras_json(poses, tmp_path)
    assert result["camera_count"] == 4


def test_cameras_json_structure(tmp_path):
    poses = _fake_poses(3)
    generate_cameras_json(poses, tmp_path)
    import json

    data = json.loads((tmp_path / "sparse" / "cameras.json").read_text())
    assert "count" in data
    assert "centers" in data
    assert len(data["centers"]) == 3
    assert all(len(c) == 3 for c in data["centers"])


# ── Semantic viewer artifacts ─────────────────────────────────────────────────


def test_semantic_copies_ply_to_subdir(tmp_path):
    # Create a fake semantic_mesh.ply at root
    (tmp_path / "semantic_mesh.ply").write_bytes(b"PLY_FAKE")
    result = generate_semantic_viewer_artifacts(tmp_path / "semantic_mesh.ply", tmp_path)
    assert result["available"] is True
    assert (tmp_path / "semantic" / "semantic_mesh.ply").is_file()


def test_semantic_does_not_delete_original(tmp_path):
    src = tmp_path / "semantic_mesh.ply"
    src.write_bytes(b"PLY_ORIGINAL")
    generate_semantic_viewer_artifacts(src, tmp_path)
    assert src.exists() and src.read_bytes() == b"PLY_ORIGINAL"


def test_semantic_missing_returns_unavailable(tmp_path):
    result = generate_semantic_viewer_artifacts(tmp_path / "nonexistent.ply", tmp_path)
    assert result["available"] is False


# ── generate_all_viewer_artifacts ─────────────────────────────────────────────


def test_generate_all_creates_viewer_artifacts_json(tmp_path):
    pts, cols = _random_pts(100)
    poses = _fake_poses(3)
    mesh = _make_simple_mesh()
    reconstruction = {"points": pts, "colors": cols, "poses": poses}
    # Create a fake semantic_mesh.ply
    (tmp_path / "semantic_mesh.ply").write_bytes(b"PLY_SEM")

    report = generate_all_viewer_artifacts(tmp_path, reconstruction, pts, cols, mesh)

    assert (tmp_path / "viewer_artifacts.json").is_file()
    assert "sparse" in report
    assert "dense_display" in report
    assert "confidence" in report
    assert "cameras" in report
    assert "semantic" in report
