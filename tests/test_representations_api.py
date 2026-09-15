"""
Tests for GET /api/jobs/{jid}/representations endpoint.
Verifies canonical descriptor structure, availability derivation from
artifact files + manifest validation status, and URL formation.
"""

import json
import shutil
import uuid

import pytest
from fastapi.testclient import TestClient

from app.db import init_db
from app.main import DATA, app

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def init():
    init_db()


@pytest.fixture
def client():
    return TestClient(app)


def _make_completed_job(jid: str | None = None) -> str:
    """Create a completed job in the DB and return its jid."""
    import time

    from app.db import Job, Session

    jid = jid or str(uuid.uuid4())
    with Session.begin() as s:
        j = Job(id=jid, name="Test job", options={"engine": "cpu", "max_frames": 60})
        j.status = "completed"
        j.progress = 100
        j.message = "Done"
        j.updated = time.time()
        s.add(j)
    return jid


def _populate_outputs(jid: str, files: list[str], manifest_validation: dict | None = None):
    """Create the output directory structure for a job."""
    out = DATA / jid / "work" / "outputs"
    out.mkdir(parents=True, exist_ok=True)

    for rel in files:
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"PLACEHOLDER")

    if manifest_validation is not None:
        manifest = {"validation_results": manifest_validation}
        (out / "manifest.json").write_text(json.dumps(manifest))

    return out


@pytest.fixture(autouse=True)
def cleanup_jobs(request):
    """Remove job directories after each test."""
    jids = []

    def register(jid):
        jids.append(jid)
        return jid

    yield register

    for jid in jids:
        shutil.rmtree(DATA / jid, ignore_errors=True)


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_representations_requires_completed_job(client, cleanup_jobs):
    """Should return 409 for non-completed jobs."""
    import time

    from app.db import Job, Session

    jid = cleanup_jobs(str(uuid.uuid4()))
    with Session.begin() as s:
        j = Job(id=jid, name="r", options={"engine": "cpu", "max_frames": 60})
        j.status = "running"
        j.updated = time.time()
        s.add(j)

    r = client.get(f"/api/jobs/{jid}/representations")
    assert r.status_code == 409


def test_representations_returns_six_keys(client, cleanup_jobs):
    """Endpoint must return all 6 representation keys."""
    jid = cleanup_jobs(_make_completed_job())
    _populate_outputs(jid, [])

    r = client.get(f"/api/jobs/{jid}/representations")
    assert r.status_code == 200
    body = r.json()
    for key in ("sparse", "dense", "mesh", "textured", "semantic", "confidence"):
        assert key in body, f"Key '{key}' missing from response"


def test_representations_all_unavailable_when_no_files(client, cleanup_jobs):
    """With no artifacts, all modes should be unavailable."""
    jid = cleanup_jobs(_make_completed_job())
    _populate_outputs(jid, [])

    body = client.get(f"/api/jobs/{jid}/representations").json()
    for key in ("sparse", "dense", "mesh", "textured", "semantic", "confidence"):
        assert body[key]["available"] is False, f"{key} should be unavailable"


def test_representations_sparse_available_with_ply(client, cleanup_jobs):
    """Sparse should be available when sparse/sparse.ply exists."""
    jid = cleanup_jobs(_make_completed_job())
    _populate_outputs(jid, ["sparse/sparse.ply"])

    body = client.get(f"/api/jobs/{jid}/representations").json()
    assert body["sparse"]["available"] is True
    assert "sparse/sparse.ply" in body["sparse"]["url"]


def test_representations_cameras_url_populated(client, cleanup_jobs):
    """cameras_url should be set when sparse/cameras.json exists."""
    jid = cleanup_jobs(_make_completed_job())
    _populate_outputs(jid, ["sparse/sparse.ply", "sparse/cameras.json"])

    body = client.get(f"/api/jobs/{jid}/representations").json()
    assert body["sparse"]["cameras_url"] is not None
    assert "cameras.json" in body["sparse"]["cameras_url"]


def test_representations_dense_display_preferred(client, cleanup_jobs):
    """Dense should prefer dense_display.ply over dense_filtered.ply."""
    jid = cleanup_jobs(_make_completed_job())
    _populate_outputs(jid, ["pointcloud/dense_display.ply", "dense_filtered.ply"])

    body = client.get(f"/api/jobs/{jid}/representations").json()
    assert body["dense"]["available"] is True
    assert "dense_display.ply" in body["dense"]["url"]


def test_representations_dense_fallback_to_filtered(client, cleanup_jobs):
    """Dense should fall back to dense_filtered.ply if display cloud missing."""
    jid = cleanup_jobs(_make_completed_job())
    _populate_outputs(jid, ["dense_filtered.ply"])

    body = client.get(f"/api/jobs/{jid}/representations").json()
    assert body["dense"]["available"] is True
    assert "dense_filtered.ply" in body["dense"]["url"]


def test_representations_mesh_available_with_glb(client, cleanup_jobs):
    """Mesh and Textured should be available when mesh/model.glb exists."""
    jid = cleanup_jobs(_make_completed_job())
    _populate_outputs(jid, ["mesh/model.glb"], manifest_validation={"GLB": "VERIFIED"})

    body = client.get(f"/api/jobs/{jid}/representations").json()
    assert body["mesh"]["available"] is True
    assert body["textured"]["available"] is True
    assert "model.glb" in body["mesh"]["url"]


def test_representations_mesh_unavailable_if_glb_failed(client, cleanup_jobs):
    """Mesh should be unavailable if GLB failed validation."""
    jid = cleanup_jobs(_make_completed_job())
    _populate_outputs(
        jid,
        ["mesh/model.glb"],
        manifest_validation={"GLB": "FAILED_VALIDATION: Empty geometry"},
    )

    body = client.get(f"/api/jobs/{jid}/representations").json()
    assert body["mesh"]["available"] is False
    assert body["textured"]["available"] is False


def test_representations_semantic_checks_subdir(client, cleanup_jobs):
    """Semantic should prefer outputs/semantic/semantic_mesh.ply."""
    jid = cleanup_jobs(_make_completed_job())
    _populate_outputs(jid, ["semantic/semantic_mesh.ply"])

    body = client.get(f"/api/jobs/{jid}/representations").json()
    assert body["semantic"]["available"] is True
    assert "semantic_mesh.ply" in body["semantic"]["url"]


def test_representations_semantic_legacy_path_fallback(client, cleanup_jobs):
    """Semantic should fall back to outputs/semantic_mesh.ply (legacy path)."""
    jid = cleanup_jobs(_make_completed_job())
    _populate_outputs(jid, ["semantic_mesh.ply"])

    body = client.get(f"/api/jobs/{jid}/representations").json()
    assert body["semantic"]["available"] is True


def test_representations_semantic_includes_palette(client, cleanup_jobs):
    """Semantic response must include class palette."""
    jid = cleanup_jobs(_make_completed_job())
    _populate_outputs(jid, ["semantic/semantic_mesh.ply"])

    body = client.get(f"/api/jobs/{jid}/representations").json()
    assert "palette" in body["semantic"]
    assert "BUILDING" in body["semantic"]["palette"]


def test_representations_confidence_available_with_ply(client, cleanup_jobs):
    """Confidence should be available when mesh/confidence_mesh.ply exists."""
    jid = cleanup_jobs(_make_completed_job())
    _populate_outputs(jid, ["mesh/confidence_mesh.ply"])

    body = client.get(f"/api/jobs/{jid}/representations").json()
    assert body["confidence"]["available"] is True
    assert "confidence_mesh.ply" in body["confidence"]["url"]


def test_representations_confidence_includes_palette(client, cleanup_jobs):
    """Confidence response must include support palette."""
    jid = cleanup_jobs(_make_completed_job())
    _populate_outputs(jid, ["mesh/confidence_mesh.ply"])

    body = client.get(f"/api/jobs/{jid}/representations").json()
    assert "palette" in body["confidence"]
    assert "SUPPORTED" in body["confidence"]["palette"]
    assert "WEAK" in body["confidence"]["palette"]
    assert "UNOBSERVED" in body["confidence"]["palette"]


def test_representations_urls_use_nested_artifact_route(client, cleanup_jobs):
    """All URLs must use /api/jobs/{jid}/files/... nested route."""
    jid = cleanup_jobs(_make_completed_job())
    _populate_outputs(
        jid,
        [
            "sparse/sparse.ply",
            "pointcloud/dense_display.ply",
            "mesh/model.glb",
            "semantic/semantic_mesh.ply",
            "mesh/confidence_mesh.ply",
        ],
        manifest_validation={"GLB": "VERIFIED"},
    )

    body = client.get(f"/api/jobs/{jid}/representations").json()
    for key, rep in body.items():
        if rep.get("url"):
            assert rep["url"].startswith(f"/api/jobs/{jid}/files/"), f"{key} URL malformed: {rep['url']}"


def test_representations_no_path_traversal(client, cleanup_jobs):
    """viewer_artifacts.json must not expose traversal paths."""
    jid = cleanup_jobs(_make_completed_job())
    out = _populate_outputs(jid, ["sparse/sparse.ply"])

    # Place a viewer_artifacts.json with a traversal path (should be ignored by file_info)
    va = {"sparse": {"available": True, "path": "../../../../etc/passwd"}}
    (out / "viewer_artifacts.json").write_text(json.dumps(va))

    # The endpoint uses its own file_info() check, not the path from viewer_artifacts.json directly
    body = client.get(f"/api/jobs/{jid}/representations").json()
    # sparse.ply does exist, so it should still show available
    assert body["sparse"]["available"] is True
    # URL must be safe
    if body["sparse"].get("url"):
        assert ".." not in body["sparse"]["url"]


def test_representations_bytes_populated(client, cleanup_jobs):
    """bytes field should be populated for available representations."""
    jid = cleanup_jobs(_make_completed_job())
    _populate_outputs(jid, ["sparse/sparse.ply"])

    body = client.get(f"/api/jobs/{jid}/representations").json()
    assert body["sparse"]["bytes"] is not None
    assert body["sparse"]["bytes"] > 0
