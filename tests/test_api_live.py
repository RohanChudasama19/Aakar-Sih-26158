from fastapi.testclient import TestClient

from app.db import init_db
from app.main import app

init_db()
client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "queue" in data
    assert "capabilities" in data


def test_jobs_list():
    response = client.get("/api/jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_job_not_found():
    response = client.get("/api/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_samples_endpoint():
    response = client.get("/api/samples/sample.mp4")
    assert response.status_code == 200

    response = client.get("/api/samples/nonexistent.mp4")
    assert response.status_code == 404
