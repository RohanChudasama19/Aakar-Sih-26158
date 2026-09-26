from pathlib import Path
import json, csv
from PIL import Image
import statistics

# Inspect MARS-LVIG HKairport01 FAST frames for visual quality
mars_imgs = Path("data_external/mars_lvig/processed/HKairport01/FAST/images")
frames = sorted(mars_imgs.iterdir())

# Sample sharpness using Laplacian variance
import cv2, numpy as np
sharpness_vals = []
for f in frames[::20]:  # sample every 20th frame
    img = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE)
    if img is not None:
        lap = cv2.Laplacian(img, cv2.CV_64F).var()
        sharpness_vals.append(lap)

print(f"MARS-LVIG HKairport01 FAST frame quality:")
print(f"  Sampled frames: {len(sharpness_vals)}")
print(f"  Sharpness (Laplacian var): min={min(sharpness_vals):.0f} mean={statistics.mean(sharpness_vals):.0f} max={max(sharpness_vals):.0f}")
print(f"  Low sharpness (<100): {sum(1 for s in sharpness_vals if s < 100)}")
print()

# GPS coverage
gps_path = Path("data_external/mars_lvig/processed/HKairport01/FAST/gps.csv")
rows = list(csv.reader(gps_path.open()))
lats = [float(r[2]) for r in rows[1:]]
lons = [float(r[3]) for r in rows[1:]]
# Bounding box in meters (rough)
lat_span_m = (max(lats) - min(lats)) * 111111
lon_span_m = (max(lons) - min(lons)) * 111111 * 0.906  # cos(22.4)
print(f"Scene coverage: ~{lat_span_m:.0f}m x {lon_span_m:.0f}m")
print(f"Location: Hong Kong International Airport area")

# Check manifest for duration
manifest = json.loads(Path("data_external/mars_lvig/processed/HKairport01/manifest.json").read_text())
print(f"Duration: {manifest['duration']:.1f}s ({manifest['duration']/60:.1f} min)")
print(f"Camera fps: {manifest['camera_fps']}")
print(f"Camera frames total: {manifest['camera_frame_count']}")
print(f"Extracted (FAST subset): {len(frames)} frames")
print(f"GNSS topic: {manifest['gnss_topic']}")
print(f"Source provenance: {manifest['source_provenance']}")
