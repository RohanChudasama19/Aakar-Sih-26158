import io
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import telemetry
ROOT=Path(__file__).resolve().parents[1]

def test_required_uploads_and_checkpoint_trust_gate():
    with TestClient(app) as c:
        assert c.get('/api/health').json()['queue']['available']
        assert c.post('/api/jobs').status_code==422
        files={k:(name,b'not empty') for k,name in [('video','clip.mp4'),('gps','gps.csv'),('flight','flight.json'),('segmentation','evil.pt')]}
        r=c.post('/api/jobs',files=files)
        assert r.status_code==422 and 'disabled' in r.json()['detail']

def test_missing_job_and_invalid_engine():
    with TestClient(app) as c:
        assert c.get('/api/jobs/invalid').status_code==404
        files={k:(name,b'nonempty') for k,name in [('video','clip.mp4'),('gps','gps.csv'),('flight','flight.json')]}
        assert c.post('/api/jobs',files=files,data={'engine':'fabricated'}).status_code==422

def test_bad_telemetry_rejected(tmp_path):
    p=tmp_path/'gps.csv';p.write_text('frame,latitude\n0,23\n')
    with pytest.raises(ValueError,match='columns'): telemetry(p)

def test_nonmonotonic_telemetry_rejected(tmp_path):
    rows=(ROOT/'samples/gps.csv').read_text().splitlines(); rows[2]=rows[1]
    p=tmp_path/'gps.csv';p.write_text('\n'.join(rows))
    with pytest.raises(ValueError,match='increasing'): telemetry(p)

def test_shared_token_protects_api(monkeypatch):
    import app.main as main
    monkeypatch.setattr(main,'API_TOKEN','test-secret')
    with TestClient(app) as c:
        assert c.get('/api/health').status_code==401
        assert c.get('/api/health',headers={'Authorization':'Bearer test-secret'}).status_code==200
