import requests, hashlib

def sha(p):
    h = hashlib.sha256()
    with open(p,'rb') as f:
        [h.update(c) for c in iter(lambda: f.read(65536), b'')]
    return h.hexdigest()

base = "http://127.0.0.1:8000"

# Test all key API endpoints
endpoints = [
    ("GET", "/api/jobs", None),
    ("GET", "/api/jobs/mars_hkairport01_quality", None),
    ("GET", "/api/jobs/mars_hkairport01_quality/files/model.glb", None),
    ("GET", "/api/jobs/mars_hkairport01_quality/files/cloud_relative.ply", None),
    ("GET", "/api/jobs/95f51b12-b771-47bf-9201-c3700f9475a7", None),
    ("GET", "/api/jobs/95f51b12-b771-47bf-9201-c3700f9475a7/files/model.glb", None),
    ("GET", "/api/health", None),
]

print("=== API ENDPOINT STATUS ===")
for method, path, body in endpoints:
    try:
        r = requests.get(base + path, timeout=60, stream=True)
        size = 0
        sha256 = "N/A"
        if r.status_code == 200 and 'model.glb' in path or '.ply' in path:
            content = r.content
            size = len(content)
            sha256 = hashlib.sha256(content).hexdigest()[:16]
        print(f"  {method} {path}: {r.status_code} {size if size else ''}  sha={sha256 if sha256 != 'N/A' else ''}")
    except Exception as e:
        print(f"  {method} {path}: ERROR - {e}")
