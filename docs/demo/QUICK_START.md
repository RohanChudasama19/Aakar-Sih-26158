# AAKAR DEMONSTRATION QUICK START

## Prerequisites
1. Redis running (edis-server)
2. Python environment activated (.venv\Scripts\activate)
3. FastAPI running (uvicorn app.main:app --reload)
4. Vite built & served or running on 5173

## Pre-flight Checklist
- Open http://127.0.0.1:8000
- Ensure "MARS HK Airport" project exists.
- Ensure "Colorado Degraded Case" exists.

## Demo Flow
1. Home / Projects -> Show list
2. New Reconstruction Wizard -> Run through steps but don't submit unless workers are explicitly online.
3. MARS Model -> Show Orbit, Walk, Heatmaps (Point Density, Support).
4. Colorado Model -> Show Heatmaps adapting to degraded topology.
