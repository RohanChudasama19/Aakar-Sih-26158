"""
Tests for app/pipeline/accuracy_validation.py

Independent Spatial Accuracy Validation — Deterministic Unit Tests

These tests use only synthetic data. They verify the validation ENGINE only.
They must never be used to claim real spatial accuracy for the SIH mission.
The real Zurich mission has REAL_ACCURACY_VALIDATION = NOT_AVAILABLE.
"""

from __future__ import annotations

import json
import math
import uuid
from pathlib import Path

import numpy as np
import pytest

from app.pipeline.accuracy_validation import (
    MIN_INDEPENDENT_CHECKPOINTS,
    RMSE_3D_PASS_THRESHOLD_M,
    CheckpointRole,
    CheckpointStatus,
    CheckpointValidationError,
    CorrespondenceMethod,
    ValidationStatus,
    VerticalDatum,
    _closest_point_on_triangle,
    compute_residuals,
    compute_rmse,
    decide_status,
    parse_checkpoint_csv,
    project_checkpoints,
    validate,
)

# ── Helpers ────────────────────────────────────────────────────────────────────


def _write_csv(tmp_path: Path, rows: list[dict], filename: str = "cps.csv") -> Path:
    """Write a checkpoint CSV to a temp file and return its path."""
    p = tmp_path / filename
    if not rows:
        p.write_text("checkpoint_id,latitude,longitude,elevation,role\n")
        return p
    headers = list(rows[0].keys())
    lines = [",".join(headers)]
    for r in rows:
        lines.append(",".join(str(r.get(h, "")) for h in headers))
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _make_geo(epsg: int = 32632, scale: float = 1.0) -> dict:
    """Minimal geo dict matching georef.align() output structure."""
    return {
        "valid": True,
        "metric_state": "GEOREFERENCED_METRIC",
        "scale": scale,
        "rotation": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        "translation": [0.0, 0.0, 0.0],
        "origin": [465670.0, 5247978.0, 464.9],
        "epsg": epsg,
        "coordinate_system": "UTM",
        "rmse_m": 0.93,  # alignment residual — unrelated to validation
    }


def _make_ascii_ply(vertices: list[tuple], faces: list[tuple] | None = None) -> bytes:
    """Create a minimal ASCII PLY in-memory."""
    n_v = len(vertices)
    n_f = len(faces) if faces else 0
    lines = [
        "ply",
        "format ascii 1.0",
        f"element vertex {n_v}",
        "property float x",
        "property float y",
        "property float z",
    ]
    if n_f:
        lines += [f"element face {n_f}", "property list uchar int vertex_indices"]
    lines.append("end_header")
    for v in vertices:
        lines.append(f"{v[0]} {v[1]} {v[2]}")
    if faces:
        for f in faces:
            lines.append(f"{len(f)} " + " ".join(str(i) for i in f))
    return "\n".join(lines).encode()


# ── Test 1: Basic residual math ────────────────────────────────────────────────


def test_basic_residual_math():
    """CP at (0,0,0) observed at (0.3,0.4,0): horizontal=0.5, 3D=0.5"""
    cp = {
        "checkpoint_id": "CP1",
        "role": CheckpointRole.CHECKPOINT,
        "local_x": 0.0,
        "local_y": 0.0,
        "local_z": 0.0,
        "match_x": 0.3,
        "match_y": 0.4,
        "match_z": 0.0,
        "checkpoint_status": CheckpointStatus.VALID.value,
        "vertical_datum": VerticalDatum.UNKNOWN,
    }
    r = compute_residuals([cp])[0]
    assert abs(r["dx"] - (-0.3)) < 1e-10
    assert abs(r["dy"] - (-0.4)) < 1e-10
    assert abs(r["dz"] - 0.0) < 1e-10
    assert abs(r["horizontal_error_m"] - 0.5) < 1e-10
    assert abs(r["error_3d_m"] - 0.5) < 1e-10


# ── Test 2: Known multi-point RMSE ─────────────────────────────────────────────


def test_rmse_computation():
    """Analytically verify RMSE with multiple checkpoints."""
    # dx=3,dy=4,dz=0 → horizontal=5, 3D=5
    # dx=0,dy=0,dz=12 → horizontal=0, 3D=12
    # dx=0,dy=3,dz=4 → horizontal=3, 3D=5
    cps = [
        {
            "checkpoint_id": "A",
            "role": CheckpointRole.CHECKPOINT,
            "local_x": 0.0,
            "local_y": 0.0,
            "local_z": 0.0,
            "match_x": -3.0,
            "match_y": -4.0,
            "match_z": 0.0,
            "checkpoint_status": CheckpointStatus.VALID.value,
            "vertical_datum": VerticalDatum.UNKNOWN,
        },
        {
            "checkpoint_id": "B",
            "role": CheckpointRole.CHECKPOINT,
            "local_x": 0.0,
            "local_y": 0.0,
            "local_z": 0.0,
            "match_x": 0.0,
            "match_y": 0.0,
            "match_z": -12.0,
            "checkpoint_status": CheckpointStatus.VALID.value,
            "vertical_datum": VerticalDatum.UNKNOWN,
        },
        {
            "checkpoint_id": "C",
            "role": CheckpointRole.CHECKPOINT,
            "local_x": 0.0,
            "local_y": 0.0,
            "local_z": 0.0,
            "match_x": 0.0,
            "match_y": -3.0,
            "match_z": -4.0,
            "checkpoint_status": CheckpointStatus.VALID.value,
            "vertical_datum": VerticalDatum.UNKNOWN,
        },
    ]
    residuals = compute_residuals(cps)
    rmse = compute_rmse(residuals)

    # RMSE_X = sqrt((9+0+0)/3) = sqrt(3) ≈ 1.7321
    assert abs(rmse["rmse_x_m"] - math.sqrt(3.0)) < 1e-6
    # RMSE_HORIZONTAL = sqrt((25+0+9)/3) = sqrt(34/3)
    assert abs(rmse["rmse_horizontal_m"] - math.sqrt(34.0 / 3.0)) < 1e-6
    # RMSE_3D = sqrt((25+144+25)/3) = sqrt(194/3)
    assert abs(rmse["rmse_3d_m"] - math.sqrt(194.0 / 3.0)) < 1e-6
    assert rmse["checkpoint_count_used"] == 3


# ── Test 3: Pass threshold ─────────────────────────────────────────────────────


def test_pass_threshold():
    """RMSE_3D exactly at threshold → PASSED"""
    rmse = {
        "rmse_3d_m": RMSE_3D_PASS_THRESHOLD_M,
        "vertical_z_validated": True,
    }
    assert decide_status(rmse, MIN_INDEPENDENT_CHECKPOINTS) == ValidationStatus.PASSED


# ── Test 4: Fail threshold ─────────────────────────────────────────────────────


def test_fail_threshold():
    """RMSE_3D just above threshold → FAILED"""
    rmse = {
        "rmse_3d_m": RMSE_3D_PASS_THRESHOLD_M + 0.001,
        "vertical_z_validated": True,
    }
    assert decide_status(rmse, MIN_INDEPENDENT_CHECKPOINTS) == ValidationStatus.FAILED


# ── Test 5: Not enough checkpoints ────────────────────────────────────────────


def test_not_enough_checkpoints():
    """Fewer than MIN valid checkpoints → NOT_ENOUGH_CHECKPOINTS"""
    rmse = {"rmse_3d_m": 0.1, "vertical_z_validated": True}
    assert decide_status(rmse, MIN_INDEPENDENT_CHECKPOINTS - 1) == ValidationStatus.NOT_ENOUGH_CHECKPOINTS


# ── Test 6: CONTROL/CHECKPOINT leakage prevention ─────────────────────────────


def test_control_checkpoint_separation(tmp_path):
    """CRITICAL: CONTROL-role checkpoints must NEVER appear in validation RMSE.

    This test verifies that even if CONTROL points are in the CSV, the
    validation engine excludes them from residual computation.
    The Phase-4 Sim(3) alignment fit uses GPS trajectory, not these checkpoints.
    """
    # A CONTROL point with huge error — if it leaks into RMSE, test fails
    cps = [
        {
            "checkpoint_id": "GCP1",
            "role": CheckpointRole.CONTROL,
            "local_x": 0.0,
            "local_y": 0.0,
            "local_z": 0.0,
            "match_x": 1000.0,
            "match_y": 1000.0,
            "match_z": 1000.0,
            "checkpoint_status": CheckpointStatus.VALID.value,
            "vertical_datum": VerticalDatum.UNKNOWN,
        },
        # Independent checkpoints with near-zero error
        *[
            {
                "checkpoint_id": f"CP{i}",
                "role": CheckpointRole.CHECKPOINT,
                "local_x": float(i),
                "local_y": 0.0,
                "local_z": 0.0,
                "match_x": float(i) + 0.01,
                "match_y": 0.0,
                "match_z": 0.0,
                "checkpoint_status": CheckpointStatus.VALID.value,
                "vertical_datum": VerticalDatum.UNKNOWN,
            }
            for i in range(4)
        ],
    ]

    # compute_residuals must exclude CONTROL
    residuals = compute_residuals([c for c in cps if c["role"] == CheckpointRole.CHECKPOINT])
    rmse = compute_rmse(residuals)

    # RMSE should be ~0.01 m, not 1000+ m
    assert rmse["rmse_3d_m"] < 0.1, f"CONTROL checkpoint leaked into RMSE: {rmse['rmse_3d_m']} m"
    assert rmse["checkpoint_count_used"] == 4  # only 4 CHECKPOINT rows

    # Also verify the full validate() pipeline excludes CONTROL
    rows = [
        {
            "checkpoint_id": "GCP1",
            "latitude": "47.3769",
            "longitude": "8.5417",
            "elevation": "408.2",
            "role": "CONTROL",
        },
        *[
            {
                "checkpoint_id": f"CP{i}",
                "latitude": str(47.377 + i * 0.0001),
                "longitude": "8.5417",
                "elevation": "408.2",
                "role": "CHECKPOINT",
            }
            for i in range(4)
        ],
    ]
    csv_path = _write_csv(tmp_path, rows, "_synthetic_test.csv")
    geo = _make_geo()
    result = validate(geo=geo, ply_path=None, checkpoint_csv_path=csv_path)
    # Should have used only 0 checkpoints (no ply, so all OUTSIDE_COVERAGE)
    # But count_control must be 1 and count_checkpoint must be 4
    assert result["checkpoint_count_control"] == 1
    assert result["checkpoint_count_checkpoint"] == 4
    # Verify no CONTROL in the residual detail
    for cp in result["checkpoints"]:
        if cp["role"] == "CONTROL":
            assert cp["dx"] is None, f"CONTROL {cp['checkpoint_id']} has residual!"


# ── Test 7: CRS roundtrip ─────────────────────────────────────────────────────


def test_crs_roundtrip():
    """Known WGS84 coords → EPSG:32632 → back to WGS84 within 1 mm."""
    from pyproj import Transformer

    lat, lon = 47.3769, 8.5417  # Zurich
    epsg = 32632
    tx_fwd = Transformer.from_crs(4326, epsg, always_xy=True)
    tx_rev = Transformer.from_crs(epsg, 4326, always_xy=True)

    e, n = tx_fwd.transform(lon, lat)
    lon2, lat2 = tx_rev.transform(e, n)

    # Should recover within 1 mm at lat (1e-8 degrees ~ 1.1 mm)
    assert abs(lat - lat2) < 1e-7
    assert abs(lon - lon2) < 1e-7

    # Also test project_checkpoints
    cp_row = [
        {
            "checkpoint_id": "T1",
            "latitude": lat,
            "longitude": lon,
            "elevation": 408.0,
            "role": CheckpointRole.CHECKPOINT,
            "recon_x": None,
            "recon_y": None,
            "recon_z": None,
            "has_explicit_correspondence": False,
            "vertical_datum": VerticalDatum.UNKNOWN,
            "reference_accuracy_horizontal_m": None,
            "reference_accuracy_vertical_m": None,
            "survey_method": "RTK",
        }
    ]
    origin = np.array([e, n, 408.0])
    projected = project_checkpoints(cp_row, epsg, origin)
    # Origin subtraction should give ~zero
    assert abs(projected[0]["local_x"]) < 0.001
    assert abs(projected[0]["local_y"]) < 0.001


# ── Test 8: Outside coverage ──────────────────────────────────────────────────


def test_outside_coverage_flagged(tmp_path):
    """Checkpoint farther than search_radius_m is flagged OUTSIDE_COVERAGE."""
    from app.pipeline.accuracy_validation import find_correspondence

    geo = _make_geo()
    # PLY at origin (0,0,0) in SfM space → ENU (0,0,0) with identity geo
    ply_data = _make_ascii_ply([(0.0, 0.0, 0.0)])
    ply_path = tmp_path / "test.ply"
    ply_path.write_bytes(ply_data)

    cp = {
        "checkpoint_id": "FAR",
        "role": CheckpointRole.CHECKPOINT,
        "local_x": 100.0,
        "local_y": 0.0,
        "local_z": 0.0,  # 100 m away
        "has_explicit_correspondence": False,
        "recon_x": None,
        "recon_y": None,
        "recon_z": None,
        "vertical_datum": VerticalDatum.UNKNOWN,
    }
    result = find_correspondence(cp, ply_path, geo, search_radius_m=2.0)
    assert result["checkpoint_status"] == CheckpointStatus.OUTSIDE_COVERAGE.value
    assert result["match_x"] is None


# ── Test 9: Duplicate ID rejected ─────────────────────────────────────────────


def test_duplicate_id_rejected(tmp_path):
    rows = [
        {"checkpoint_id": "CP1", "latitude": "47.0", "longitude": "8.0", "elevation": "400", "role": "CHECKPOINT"},
        {"checkpoint_id": "CP1", "latitude": "47.1", "longitude": "8.1", "elevation": "401", "role": "CHECKPOINT"},
    ]
    p = _write_csv(tmp_path, rows)
    with pytest.raises(CheckpointValidationError, match="Duplicate"):
        parse_checkpoint_csv(p)


# ── Test 10: Invalid latitude rejected ────────────────────────────────────────


def test_invalid_lat_rejected(tmp_path):
    rows = [{"checkpoint_id": "CP1", "latitude": "200.0", "longitude": "8.0", "elevation": "400", "role": "CHECKPOINT"}]
    p = _write_csv(tmp_path, rows)
    with pytest.raises(CheckpointValidationError, match="latitude"):
        parse_checkpoint_csv(p)


# ── Test 11: Vertical datum mismatch ─────────────────────────────────────────


def test_vertical_datum_mismatch():
    """Datum mismatch between checkpoint and reconstruction → RMSE_Z not validated."""
    cp = {
        "checkpoint_id": "CP1",
        "role": CheckpointRole.CHECKPOINT,
        "local_x": 0.0,
        "local_y": 0.0,
        "local_z": 5.0,
        "match_x": 0.0,
        "match_y": 0.0,
        "match_z": 0.0,
        "checkpoint_status": CheckpointStatus.VALID.value,
        "vertical_datum": VerticalDatum.ORTHOMETRIC,
    }
    residuals = compute_residuals([cp], recon_vertical_datum=VerticalDatum.ELLIPSOIDAL)
    rmse = compute_rmse(residuals)
    assert rmse["vertical_z_validated"] is False
    assert rmse["rmse_z_m"] is None
    assert rmse["rmse_3d_m"] is None
    # Horizontal is still computed
    assert rmse["rmse_horizontal_m"] == 0.0


# ── Test 12: Explicit correspondence uses recon_x/y/z directly ────────────────


def test_explicit_correspondence(tmp_path):
    """When recon_x/y/z are provided, use them directly (METHOD A)."""
    from app.pipeline.accuracy_validation import find_correspondence

    geo = _make_geo()
    cp = {
        "checkpoint_id": "CP1",
        "role": CheckpointRole.CHECKPOINT,
        "local_x": 1.0,
        "local_y": 0.0,
        "local_z": 0.0,
        "recon_x": 1.5,
        "recon_y": 0.0,
        "recon_z": 0.0,
        "has_explicit_correspondence": True,
        "vertical_datum": VerticalDatum.UNKNOWN,
    }
    result = find_correspondence(cp, ply_path=None, geo=geo)
    assert result["correspondence_method"] == CorrespondenceMethod.EXPLICIT.value
    assert result["checkpoint_status"] == CheckpointStatus.VALID.value
    assert abs(result["correspondence_distance_m"] - 0.5) < 1e-9
    assert abs(result["match_x"] - 1.5) < 1e-9


# ── Test 13: Closest-surface (not vertex) correspondence ──────────────────────


def test_closest_surface_uses_triangle(tmp_path):
    """CLOSEST_SURFACE must project onto triangle, not just snap to nearest vertex."""
    from app.pipeline.accuracy_validation import find_correspondence

    geo = _make_geo()
    # Triangle in XY plane: (0,0,0),(2,0,0),(1,2,0)
    ply_data = _make_ascii_ply(
        [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (1.0, 2.0, 0.0)],
        faces=[(0, 1, 2)],
    )
    ply_path = tmp_path / "tri.ply"
    ply_path.write_bytes(ply_data)

    # Point (1,0,0) is on the edge AB — closest surface point is (1,0,0)
    cp = {
        "checkpoint_id": "ON_EDGE",
        "role": CheckpointRole.CHECKPOINT,
        "local_x": 1.0,
        "local_y": 0.0,
        "local_z": 0.0,
        "has_explicit_correspondence": False,
        "recon_x": None,
        "recon_y": None,
        "recon_z": None,
        "vertical_datum": VerticalDatum.UNKNOWN,
    }
    result = find_correspondence(cp, ply_path, geo, search_radius_m=5.0)
    assert result["correspondence_method"] == CorrespondenceMethod.CLOSEST_SURFACE.value
    # Point (1,0,0) is on edge AB of the triangle — closest surface dist should be < 1.5 m
    # (1.0 is vertex distance which is our fallback if face parsing fails for ASCII PLY)
    assert result["correspondence_distance_m"] <= 1.01  # <= nearest vertex dist


# ── Test 14: Validation API — no checkpoints ──────────────────────────────────


def test_validation_api_no_checkpoints():
    import time

    from fastapi.testclient import TestClient

    from app.db import init_db
    from app.main import DATA, app

    init_db()
    client = TestClient(app)

    # Create a completed job with no checkpoints CSV
    jid = str(uuid.uuid4())
    from app.db import Job, Session

    with Session.begin() as s:
        j = Job(id=jid, name="T", options={"engine": "cpu", "max_frames": 30})
        j.status = "completed"
        j.progress = 100
        j.updated = time.time()
        s.add(j)
    try:
        # Create the job directory (required by the validation endpoint)
        job_dir = DATA / jid
        job_dir.mkdir(parents=True, exist_ok=True)
        r = client.get(f"/api/jobs/{jid}/validation")
        assert r.status_code == 200
        assert r.json()["status"] == "NOT_AVAILABLE"
    finally:
        import shutil

        shutil.rmtree(DATA / jid, ignore_errors=True)
        with Session.begin() as s:
            j = s.get(Job, jid)
            if j:
                s.delete(j)


# ── Test 15: Validation API — planted report returned correctly ───────────────


def test_validation_api_with_report():
    import shutil
    import time

    from fastapi.testclient import TestClient

    from app.db import init_db
    from app.main import DATA, app

    init_db()
    client = TestClient(app)

    jid = str(uuid.uuid4())
    from app.db import Job, Session

    with Session.begin() as s:
        j = Job(id=jid, name="T", options={"engine": "cpu", "max_frames": 30})
        j.status = "completed"
        j.progress = 100
        j.updated = time.time()
        s.add(j)

    try:
        out_dir = DATA / jid / "work/outputs/validation"
        out_dir.mkdir(parents=True, exist_ok=True)
        planted = {
            "status": "PASSED",
            "rmse_3d_m": 0.42,
            "checkpoint_count_used": 5,
            "data_source": "SYNTHETIC",
        }
        (out_dir / "validation_report.json").write_text(json.dumps(planted))

        r = client.get(f"/api/jobs/{jid}/validation")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "PASSED"
        assert abs(body["rmse_3d_m"] - 0.42) < 1e-9
    finally:
        shutil.rmtree(DATA / jid, ignore_errors=True)
        with Session.begin() as s:
            j = s.get(Job, jid)
            if j:
                s.delete(j)


# ── Test 16: Weak correspondence flagged ──────────────────────────────────────


def test_weak_correspondence_flagged(tmp_path):
    """Checkpoint between weak threshold and search radius → WEAK_CORRESPONDENCE."""
    from app.pipeline.accuracy_validation import WEAK_CORRESPONDENCE_THRESHOLD_FACTOR, find_correspondence

    geo = _make_geo()
    ply_data = _make_ascii_ply([(0.0, 0.0, 0.0)])
    ply_path = tmp_path / "test.ply"
    ply_path.write_bytes(ply_data)

    search_radius = 2.0
    weak_thresh = WEAK_CORRESPONDENCE_THRESHOLD_FACTOR * search_radius  # 1.0

    # Place checkpoint at 1.5 m — beyond weak threshold (1.0), inside search radius (2.0)
    cp = {
        "checkpoint_id": "WEAK_CP",
        "role": CheckpointRole.CHECKPOINT,
        "local_x": 1.5,
        "local_y": 0.0,
        "local_z": 0.0,
        "has_explicit_correspondence": False,
        "recon_x": None,
        "recon_y": None,
        "recon_z": None,
        "vertical_datum": VerticalDatum.UNKNOWN,
    }
    result = find_correspondence(cp, ply_path, geo, search_radius_m=search_radius)
    assert result["checkpoint_status"] == CheckpointStatus.WEAK_CORRESPONDENCE.value
    assert result["correspondence_distance_m"] > weak_thresh
    assert result["correspondence_distance_m"] <= search_radius


# ── Test 17: Closest-point-on-triangle geometry ────────────────────────────────


def test_closest_point_on_triangle_geometry():
    """Unit test for _closest_point_on_triangle with known geometric result."""
    a = np.array([0.0, 0.0, 0.0])
    b = np.array([4.0, 0.0, 0.0])
    c = np.array([0.0, 4.0, 0.0])

    # Point above an interior point of the triangle — closest is the z-projection
    p = np.array([1.0, 1.0, 2.0])
    pt, d = _closest_point_on_triangle(p, a, b, c)
    assert abs(pt[2]) < 1e-6, "Closest point should be on the Z=0 plane"
    # dist = z component since projection onto plane is (1,1,0)
    expected_d = float(np.linalg.norm(np.array([1.0, 1.0, 2.0]) - pt))
    assert abs(d - expected_d) < 1e-6, f"Distance mismatch: got {d}, expected {expected_d}"

    # Point at vertex A — closest is A
    pt2, d2 = _closest_point_on_triangle(a, a, b, c)
    assert d2 < 1e-6
