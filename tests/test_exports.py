import tempfile
from pathlib import Path

import laspy
import numpy as np
import pytest
import rasterio
import trimesh

from app.pipeline.exports import ExportManager


@pytest.fixture
def dummy_data():
    points = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.float32)
    colors = np.array([[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 255]], dtype=np.uint8)
    labels = np.array([1, 2, 3, 6], dtype=np.uint8)
    mesh = trimesh.Trimesh(vertices=points, faces=[[0, 1, 2], [0, 2, 3]])
    geo = {
        "valid": True,
        "epsg": 32633,
        "origin": np.array([500000.0, 4600000.0, 100.0]),
        "scale": 1.0,
        "rotation": np.eye(3),
        "translation": np.zeros(3),
        "metric_state": "GEOREFERENCED",
    }
    return points, colors, labels, mesh, geo


def test_export_manager_validates_and_manifests(dummy_data):
    points, colors, labels, mesh, geo = dummy_data
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        manager = ExportManager(out, geo)

        manager.export_point_cloud(points, colors, point_labels=labels)
        manager.export_mesh(mesh)
        manager.export_geospatial(points, colors)

        manifest = manager.finalize()

        assert (out / "manifest.json").exists()

        # Verify sizes and checksums
        assert "cloud_metric.ply" in manifest["generated_files"]
        assert manifest["generated_files"]["cloud_metric.ply"]["size_bytes"] > 0
        assert len(manifest["generated_files"]["cloud_metric.ply"]["sha256"]) == 64

        # Verify validation states
        assert manifest["validation_results"]["PLY_METRIC"] == "VERIFIED"
        assert manifest["validation_results"]["GLB"] == "VERIFIED"
        assert manifest["validation_results"]["LAS"] == "VERIFIED"
        assert manifest["validation_results"]["GeoTIFF_DSM"] == "VERIFIED"

        # Roundtrip LAS
        las_path = out / "pointcloud/cloud.las"
        assert las_path.exists()
        las_data = laspy.read(las_path)
        assert len(las_data.points) == 4
        # Verify CRS was preserved
        assert las_data.header.parse_crs().to_epsg() == geo["epsg"]

        # Verify DSM metadata
        dsm_path = out / "geospatial/dsm.tif"
        with rasterio.open(dsm_path) as src:
            assert src.crs.to_epsg() == geo["epsg"]
            assert src.count == 1
            assert src.width > 0
            assert src.height > 0

        # Verify GLB
        glb_path = out / "mesh/model.glb"
        reloaded_mesh = trimesh.load(glb_path)
        assert len(reloaded_mesh.geometry) > 0

        # Check that semantic labels mapped to LAS classification correctly
        # 1->2 (Ground), 2->11 (Road), 3->6 (Building), 6->1 (Infrastructure)
        expected_classes = [2, 11, 6, 1]
        np.testing.assert_array_equal(las_data.classification, expected_classes)
