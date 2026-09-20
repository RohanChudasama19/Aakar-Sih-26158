import pytest
import numpy as np
from pathlib import Path
from app.pipeline.control_geometry import (
    GroundControlPoint,
    ControlRole,
    VerticalDatum,
    GeometryQuality,
    check_control_geometry,
    fit_control_alignment
)

def test_minimum_controls():
    pts = [
        GroundControlPoint("c1", 45.0, 9.0, 100.0, ControlRole.CONTROL, 0.0, 0.0, 0.0),
        GroundControlPoint("c2", 45.001, 9.0, 100.0, ControlRole.CONTROL, 1.0, 0.0, 0.0),
        GroundControlPoint("c3", 45.0, 9.001, 100.0, ControlRole.CONTROL, 0.0, 1.0, 0.0),
    ]
    quality, warnings = check_control_geometry(pts)
    assert quality == GeometryQuality.WEAK
    assert len(warnings) > 0
    assert "NOT_ENOUGH_CONTROLS" in warnings[0]

def test_checkpoint_leakage_protection(tmp_path):
    import pyproj
    tx = pyproj.Transformer.from_crs(4326, 32632, always_xy=True)
    
    # We create perfect matches
    lat0, lon0 = 45.0, 9.0
    e0, n0 = tx.transform(lon0, lat0)
    
    e1, n1 = tx.transform(lon0 + 0.001, lat0)
    e2, n2 = tx.transform(lon0, lat0 + 0.001)
    e3, n3 = tx.transform(lon0 + 0.001, lat0 + 0.001)
    
    pts = [
        GroundControlPoint("c1", lat0, lon0, 100.0, ControlRole.CONTROL, e0, n0, 100.0),
        GroundControlPoint("c2", lat0, lon0+0.001, 100.0, ControlRole.CONTROL, e1, n1, 100.0),
        GroundControlPoint("c3", lat0+0.001, lon0, 100.0, ControlRole.CONTROL, e2, n2, 100.0),
        GroundControlPoint("c4", lat0+0.001, lon0+0.001, 101.0, ControlRole.CONTROL, e3, n3, 101.0),
    ]
    quality, warnings = check_control_geometry(pts)
    assert quality == GeometryQuality.GOOD

    # Fit without checkpoint
    rep_clean = fit_control_alignment(pts, tmp_path, 32632)
    
    crazy_pt = GroundControlPoint("crazy", 80.0, 120.0, 5000.0, ControlRole.CHECKPOINT, 9999.0, 9999.0, 9999.0)
    pts.append(crazy_pt)
    
    rep = fit_control_alignment(pts, tmp_path, 32632)
    
    # Assert bitwise unchanged
    assert rep_clean["transform"]["scale"] == rep["transform"]["scale"]
    assert rep_clean["transform"]["rotation"] == rep["transform"]["rotation"]
    assert rep_clean["transform"]["translation"] == rep["transform"]["translation"]
    assert rep["CONTROL_FIT_RMSE"] < 1e-3
    assert rep["control_count"] == 4
    assert rep["checkpoint_count"] == 1

def test_weak_geometry():
    # Collinear points
    pts = [
        GroundControlPoint("c1", 45.0, 9.0, 100.0, ControlRole.CONTROL, 0.0, 0.0, 0.0),
        GroundControlPoint("c2", 45.001, 9.0, 100.0, ControlRole.CONTROL, 1.0, 0.0, 0.0),
        GroundControlPoint("c3", 45.002, 9.0, 100.0, ControlRole.CONTROL, 2.0, 0.0, 0.0),
        GroundControlPoint("c4", 45.003, 9.0, 100.0, ControlRole.CONTROL, 3.0, 0.0, 0.0),
    ]
    quality, warnings = check_control_geometry(pts)
    assert quality == GeometryQuality.WEAK
    assert any("collinear" in w for w in warnings)

def test_horizontal_only_fit(tmp_path):
    import pyproj
    tx = pyproj.Transformer.from_crs(4326, 32632, always_xy=True)
    lat0, lon0 = 45.0, 9.0
    e0, n0 = tx.transform(lon0, lat0)
    e1, n1 = tx.transform(lon0 + 0.001, lat0)
    e2, n2 = tx.transform(lon0, lat0 + 0.001)
    e3, n3 = tx.transform(lon0 + 0.001, lat0 + 0.001)
    
    # Missing vertical datum on one point drops us to horizontal mode
    pts = [
        GroundControlPoint("c1", lat0, lon0, 100.0, ControlRole.CONTROL, e0, n0, 999.0, VerticalDatum.ELLIPSOIDAL),
        GroundControlPoint("c2", lat0, lon0+0.001, 100.0, ControlRole.CONTROL, e1, n1, 999.0, VerticalDatum.ELLIPSOIDAL),
        GroundControlPoint("c3", lat0+0.001, lon0, 100.0, ControlRole.CONTROL, e2, n2, 999.0, VerticalDatum.UNKNOWN),
        GroundControlPoint("c4", lat0+0.001, lon0+0.001, 101.0, ControlRole.CONTROL, e3, n3, 999.0, VerticalDatum.ELLIPSOIDAL),
    ]
    
    rep = fit_control_alignment(pts, tmp_path, 32632)
    assert rep["mode"] == "GCP_HORIZONTAL_ONLY"
    assert rep["CONTROL_FIT_RMSE"] < 1e-3  # Should match perfectly in 2D despite wild Z mismatch
