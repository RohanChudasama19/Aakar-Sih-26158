from fastapi.testclient import TestClient

from app.db import Job, Session, init_db
from app.main import app

client = TestClient(app)


def test_cancel_api():
    init_db()
    with Session() as s:
        s.add(Job(id="test-cancel-job", name="cancel test", status="running", message="Working"))
        s.commit()

    r = client.post("/api/jobs/test-cancel-job/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "cancelling"

    with Session() as s:
        job = s.get(Job, "test-cancel-job")
        assert job.status == "cancelling"


def test_retry_api():
    init_db()
    with Session() as s:
        s.add(Job(id="test-retry-job", name="retry test", status="failed", message="Failed"))
        s.commit()

    r = client.post("/api/jobs/test-retry-job/retry")
    assert r.status_code == 200
    assert r.json()["status"] == "queued"

    with Session() as s:
        job = s.get(Job, "test-retry-job")
        assert job.status == "queued"
        assert job.progress == 0.0
