from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_map_data_relative(tmp_path, monkeypatch):
    import app.main

    monkeypatch.setattr(app.main, "DATA", tmp_path)
    jid = "test-job-relative"
    job_dir = tmp_path / jid
    job_dir.mkdir(parents=True)

    work_out = job_dir / "work/outputs"
    work_out.mkdir(parents=True)
    (work_out / "mission_report.json").write_text('{"alignment": {"metric_state": "RELATIVE"}}')

    resp = client.get(f"/api/jobs/{jid}/map-data")
    assert resp.status_code == 200
    assert resp.json()["metric_state"] == "RELATIVE"
    assert "reconstructed_trajectory" not in resp.json()


def test_map_data_georeferenced(tmp_path, monkeypatch):
    import app.main

    monkeypatch.setattr(app.main, "DATA", tmp_path)
    jid = "test-job-geo"
    job_dir = tmp_path / jid
    job_dir.mkdir(parents=True)

    work_out = job_dir / "work/outputs"
    work_out.mkdir(parents=True)

    (work_out / "mission_report.json").write_text("""{
        "alignment": {
            "metric_state": "GEOREFERENCED_METRIC",
            "epsg": 32643,
            "scale": 1.0,
            "rotation": [[1,0,0],[0,1,0],[0,0,1]],
            "translation": [0,0,0],
            "origin": [229995, 2539991, 63],
            "rmse_m": 0.5,
            "alignment_inliers": 10,
            "alignment_samples": 10
        }
    }""")

    inputs_dir = job_dir / "inputs"
    inputs_dir.mkdir()
    (inputs_dir / "gps.csv").write_text("timestamp,frame,lat,lon,alt\n2026,1,22.9,72.3,60")

    work_dir = job_dir / "work"
    (work_dir / "poses.json").write_text('{"1": [[1,0,0,0],[0,1,0,0],[0,0,1,0]]}')

    resp = client.get(f"/api/jobs/{jid}/map-data")
    assert resp.status_code == 200
    data = resp.json()
    assert data["metric_state"] == "GEOREFERENCED_METRIC"
    assert data["crs"] == "EPSG:32643"
    assert data["alignment_quality"]["rmse_m"] == 0.5
    assert len(data["gps_trajectory"]) == 1
    assert len(data["reconstructed_trajectory"]) == 1

    recon = data["reconstructed_trajectory"][0]
    assert recon["camera_id"] == "1"
    # Origin is 229995, 2539991. EPSG 32643. Let's make sure lon/lat are close to expected WGS84 for that UTM.
    assert 22.0 < recon["lat"] < 24.0
    assert 71.0 < recon["lon"] < 73.0
