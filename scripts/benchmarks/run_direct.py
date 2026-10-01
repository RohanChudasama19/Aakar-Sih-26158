import os
import shutil
import json
from pathlib import Path
from app.pipeline.runner import run_pipeline

def main():
    # We need to simulate the inputs since runner.py expects video, telemetry, flight.json etc.
    # But wait, runner.py expects a specific input directory format.
    # If the input directory lacks flight.json or gps.csv or video.mp4, it will fail.
    # Let's inspect runner.py on how it requires these files.
    pass

if __name__ == "__main__":
    main()
