# AAKAR Deployment Guide

AAKAR consists of three main components: a FastAPI server, an RQ worker, and a Redis message broker.

## System Requirements
- **Storage:** 50 MB per processed frame (e.g. 500 frames = 25 GB free workspace required).
- **GPU (Optional but highly recommended):** NVIDIA RTX 30-series or higher.

## Windows Local Deployment
1. Install Python 3.10 and create a virtual environment: python -m venv .venv
2. Activate and install: pip install -r requirements.txt
3. Download and extract **COLMAP** (with CUDA support) and add it to your Windows System PATH.
4. (Optional) Install **Blender** and add it to your PATH if FBX export is required.
5. Install and run **Redis** (via WSL2 or Windows port).
6. Start Worker: python -m app.worker
7. Start Server: uvicorn app.main:app --host 0.0.0.0 --port 8000

## Linux Deployment
1. sudo apt install colmap redis-server ffmpeg
2. pip install -r requirements.txt
3. Start Redis: sudo systemctl start redis-server
4. Start Worker: python -m app.worker
5. Start Server: uvicorn app.main:app --host 0.0.0.0 --port 8000

## Docker Deployment (Unsupported / Not Verified)
*AAKAR provides a Dockerfile, but Docker GPU passthrough for COLMAP CUDA has not been actively validated in this release cycle.* 
If using Docker, map a large volume to /app/data to ensure sufficient disk space.
