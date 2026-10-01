from pathlib import Path
import hashlib, os

# Hash the FAST_VALIDATION video
p = Path("data/FAST_VALIDATION/inputs/video.mp4")
h = hashlib.sha256()
with open(p, 'rb') as f:
    for chunk in iter(lambda: f.read(65536), b''):
        h.update(chunk)
print(f"FAST_VALIDATION video SHA256: {h.hexdigest()}")
print(f"Size: {p.stat().st_size}")
print()
# Also show video duration from flight.json
import json
fj = json.loads(Path("data/FAST_VALIDATION/inputs/flight.json").read_text())
print(f"Duration: {fj['video_duration_sec']}s")
print(f"Resolution: {fj['video_resolution']}")
print(f"FPS: {fj['video_fps']}")
print(f"Drone: {fj['drone_model']}")
print(f"Mission: {fj['mission_name']}")
print(f"Start: {fj['start_time_utc']}")
print(f"Home lat/lon: {fj['home_point']}")
