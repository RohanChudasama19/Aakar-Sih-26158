import pytest
from fastapi.testclient import TestClient

from app.db import init_db
from app.main import DATA, app

init_db()
client = TestClient(app)


@pytest.fixture
def dummy_job():
    # create a dummy job in the database and some dummy files
    job_id = "00000000-0000-0000-0000-000000000001"
    from app.db import Job, Session

    with Session() as s:
        existing = s.query(Job).filter_by(id=job_id).first()
        if not existing:
            j = Job(id=job_id, name="test", status="completed", stage="done", progress=1.0)
            s.add(j)
            s.commit()

    out_dir = DATA / job_id / "work" / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Create top level
    (out_dir / "top.txt").write_text("top")

    # Create nested mesh/model.glb
    (out_dir / "mesh").mkdir(exist_ok=True)
    (out_dir / "mesh" / "model.glb").write_text("glb")

    # Create nested reports/deliverables_matrix.json
    (out_dir / "reports").mkdir(exist_ok=True)
    (out_dir / "reports" / "deliverables_matrix.json").write_text('{"matrix": {}}')

    return job_id


def test_nested_artifact_routes(dummy_job):
    # top level
    r = client.get(f"/api/jobs/{dummy_job}/files/top.txt")
    assert r.status_code == 200
    assert r.text == "top"

    # mesh/model.glb
    r = client.get(f"/api/jobs/{dummy_job}/files/mesh/model.glb")
    assert r.status_code == 200
    assert r.text == "glb"

    # reports/deliverables_matrix.json
    r = client.get(f"/api/jobs/{dummy_job}/files/reports/deliverables_matrix.json")
    assert r.status_code == 200
    assert "matrix" in r.json()

    # missing file
    r = client.get(f"/api/jobs/{dummy_job}/files/missing.txt")
    assert r.status_code == 404

    # traversal attempt
    r = client.get(f"/api/jobs/{dummy_job}/files/../artifacts.zip")
    assert r.status_code == 404

    r = client.get(f"/api/jobs/{dummy_job}/files/mesh/../../outputs")
    assert r.status_code == 404
