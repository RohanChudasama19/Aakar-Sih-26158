import shutil
import zipfile
from pathlib import Path

import laspy
import numpy as np
import rasterio
import trimesh

from app.pipeline.runner import run_pipeline

ROOT = Path(__file__).resolve().parents[1]


def test_real_cpu_pipeline_all_stages_and_export_roundtrips(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for src, dst in [("sample.mp4", "video.mp4"), ("gps.csv", "gps.csv"), ("flight.json", "flight.json")]:
        shutil.copy(ROOT / "samples" / src, inputs / dst)
    events = []
    report = run_pipeline(
        inputs, tmp_path / "work", {"max_frames": 60, "max_width": 640}, lambda s, p, m: events.append((s, p))
    )
    out = tmp_path / "work/outputs"
    assert {s for s, p in events} == set("ABCDEF")
    assert events[-1] == ("F", 100)
    assert all(report["stages"][s]["status"] == "completed" for s in "ABCDEF")
    assert report["targets"]["coverage"]["registered_frames"] >= 8
    assert report["metric_state"] == "GEOREFERENCED_METRIC"
    assert report["targets"]["spatial_accuracy"]["passed"] is None
    assert report["targets"]["processing_time"]["ten_minute_benchmark_passed"] is None
    assert report["mesh"]["faces"] > 100
    scene = trimesh.load(out / "mesh/model.glb")
    assert len(scene.geometry) > 0
    cloud = trimesh.load(out / "pointcloud/cloud_metric.ply")
    assert len(cloud.vertices) > 100
    las = laspy.read(out / "pointcloud/cloud.las")
    assert len(las.points) == len(cloud.vertices)
    assert las.header.parse_crs().to_epsg() == report["alignment"]["epsg"]
    with rasterio.open(out / "geospatial/dsm.tif") as src:
        assert src.crs.to_epsg() == report["alignment"]["epsg"]
        assert np.count_nonzero(src.read(1) != src.nodata) > 100
    labels = np.load(out / "semantic_labels.npz")
    assert len(labels["points"]) == len(cloud.vertices)
    assert labels["point_labels"].max() <= 7
    with zipfile.ZipFile(tmp_path / "work/artifacts.zip") as z:
        assert {
            "mesh/model.glb",
            "mesh/model.obj",
            "pointcloud/cloud_metric.ply",
            "mission_report.json",
            "geospatial/dsm.tif",
            "pointcloud/cloud.las",
            "manifest.json",
            "reports/deliverables_matrix.json",
        } <= set(z.namelist())
    assert all(
        (out / f).stat().st_size > 0
        for f in [
            "mesh/model.glb",
            "mesh/model.obj",
            "pointcloud/cloud_metric.ply",
            "mission_report.json",
            "manifest.json",
        ]
    )
