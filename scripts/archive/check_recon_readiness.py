import os
import sys
import shutil
import platform
import subprocess
from app.db import Session
from app.pipeline.colmap import resolve_colmap_executable

def check():
    print("=== NEW RECONSTRUCTION READINESS ===")
    
    # 1. COLMAP
    colmap_path = resolve_colmap_executable()
    has_colmap = colmap_path is not None
    if has_colmap:
        try:
            r = subprocess.run([colmap_path, "help"], capture_output=True, text=True, timeout=5)
            has_colmap = "COLMAP" in r.stdout or "colmap" in r.stdout.lower()
        except Exception:
            has_colmap = False
    print(f"COLMAP: {'Found (' + str(colmap_path) + ')' if has_colmap else 'Missing'}")

    # 2. OpenMVS (often used in these pipelines if colmap isn't doing dense)
    openmvs_path = shutil.which("ReconstructMesh")
    has_openmvs = openmvs_path is not None
    print(f"OpenMVS: {'Found' if has_openmvs else 'Missing'}")

    # 3. GPU
    has_gpu = False
    try:
        r = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=5)
        has_gpu = r.returncode == 0
    except Exception:
        pass
    print(f"GPU (CUDA): {'Available' if has_gpu else 'Not Detected'}")

    # 4. Worker & Redis
    import redis
    has_redis = False
    try:
        rc = redis.Redis(host='localhost', port=6379, db=0)
        has_redis = rc.ping()
    except Exception:
        pass
    print(f"Redis: {'Online' if has_redis else 'Offline'}")

    # Worker via DB or health
    import requests
    try:
        health = requests.get("http://127.0.0.1:8000/api/health").json()
        workers = health.get("queue", {}).get("workers", 0)
        has_worker = workers > 0
    except:
        has_worker = False
    print(f"Worker: {'Online' if has_worker else 'Offline'}")

    # 5. Disk Space
    total, used, free = shutil.disk_usage(".")
    free_gb = free // (2**30)
    print(f"Disk Space: {free_gb} GB Free")

    # Conclusion
    if not has_colmap:
        print("Status: BLOCKED")
        print("Reason: COLMAP executable not found or not functioning. Real reconstruction cannot proceed.")
    elif not has_worker:
        print("Status: BLOCKED")
        print("Reason: RQ worker is offline.")
    elif free_gb < 10:
        print("Status: PARTIAL")
        print("Reason: Low disk space.")
    elif not has_gpu:
        print("Status: PARTIAL")
        print("Reason: No CUDA GPU detected, fallback to slow CPU processing.")
    else:
        print("Status: READY")

check()
