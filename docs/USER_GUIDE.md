# AeroRecon User Guide

## Installation
1. Install Python 3.10+.
2. Run `pip install -r requirements.txt`.
3. For CPU mode, this is sufficient.
4. For GPU mode (COLMAP), install COLMAP and add it to your PATH, then set `ENABLE_COLMAP=1` in your environment.

## Running the Server
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Then navigate to `http://localhost:8000`.

## Conducting a Mission
1. **Capture Video:** Fly the drone laterally across the subject. Avoid pure rotation.
2. **Export Telemetry:** Save the GPS flight logs (CSV).
3. **Upload:** Use the "New Mission" dialog to upload your MP4 and CSV.
4. **Analyze:** Once processing completes, use the 3D Viewer to measure paths and areas. Download deliverables for CAD or GIS software.
