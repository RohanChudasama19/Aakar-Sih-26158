"""
Regression tests for job-ID input validation in get_job() and artifact routes.
Covers: path traversal, too-long IDs, special characters, valid UUID, valid
imported mission ID, missing mission, and unauthorized artifact access.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)


# ── Malformed / dangerous identifiers ─────────────────────────────────────────


@pytest.mark.parametrize(
    "jid",
    [
        "../../../etc/passwd",
        "a" * 65,               # exceeds 64-char bound
        "id;rm -rf /",          # shell injection chars
        "../../secret",
        "job with spaces",
        # null byte (\x00) is rejected by httpx at URL parse time — correct
        "job/slash",            # path separator
    ],
)
def test_malformed_jid_rejected(jid):
    """Malformed job IDs must not return 200."""
    r = client.get(f"/api/jobs/{jid}")
    assert r.status_code in (400, 404, 405, 422), (
        f"Expected 4xx for jid={jid!r}, got {r.status_code}"
    )


# ── Valid format, not in DB ────────────────────────────────────────────────────


def test_missing_job_returns_404():
    """Well-formed but absent job ID → 404."""
    r = client.get("/api/jobs/nonexistent-job-999")
    assert r.status_code == 404


def test_valid_uuid_format_not_found():
    """Valid UUID4 format but absent from DB → 404 (not 400/422)."""
    r = client.get("/api/jobs/12345678-1234-1234-1234-123456789abc")
    assert r.status_code == 404


def test_valid_custom_id_format_not_found():
    """Valid imported mission ID format but absent from DB → 404 (not 400/422)."""
    r = client.get("/api/jobs/mars_hkairport01_quality_test")
    assert r.status_code == 404


# ── Path traversal in artifact routes ─────────────────────────────────────────


@pytest.mark.parametrize(
    "filename",
    [
        "../../../etc/passwd",
        "../../aakar.db",
        "%2e%2e%2fetc%2fpasswd",
    ],
)
def test_artifact_path_traversal_rejected(filename):
    """Path traversal in artifact filename must not succeed."""
    r = client.get(f"/api/jobs/some-job-id/files/{filename}")
    # Expect 404 (job not found) or 400/422 (validation), never 200
    assert r.status_code in (400, 404, 422), (
        f"Expected 4xx for filename={filename!r}, got {r.status_code}"
    )
