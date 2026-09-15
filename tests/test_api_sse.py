import json

import pytest
from fastapi.testclient import TestClient

from app.db import init_db
from app.main import DATA, app

init_db()
client = TestClient(app)


@pytest.fixture
def blocked_job():
    job_id = "00000000-0000-0000-0000-000000000002"
    from app.db import Job, Session

    with Session() as s:
        existing = s.query(Job).filter_by(id=job_id).first()
        if not existing:
            j = Job(id=job_id, name="test-blocked", status="RECONSTRUCTION_BLOCKED", stage="readiness", progress=0.1)
            s.add(j)
            s.commit()

    out_dir = DATA / job_id / "work"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "events.jsonl").write_text(
        json.dumps({"stage": "readiness", "progress": 0.1, "message": "Blocked"}) + "\\n"
    )

    return job_id


def test_sse_terminal_states(blocked_job):
    # Just run the event stream and ensure it terminates normally instead of blocking forever
    with client.stream("GET", f"/api/jobs/{blocked_job}/events") as response:
        assert response.status_code == 200
        lines = []
        for line in response.iter_lines():
            if line:
                lines.append(line)

        assert len(lines) > 0
        last_data = json.loads(lines[-1].replace("data: ", ""))
        assert last_data["status"] == "RECONSTRUCTION_BLOCKED"
