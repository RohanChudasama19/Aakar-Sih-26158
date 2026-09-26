from pathlib import Path
import json, os

# Analyse FAST_VALIDATION dataset
fv = Path("data/FAST_VALIDATION")
fv_inputs = fv / "inputs"
fv_orig = fv / "work" / "originals"
preprocess = fv / "work" / "preprocess.json"

# Count frames, check video
video = fv_inputs / "video.mp4"
print(f"Video: {video} exists={video.exists()} size={os.path.getsize(video) if video.exists() else 'N/A'}")

# Preprocess data 
if preprocess.exists():
    data = json.loads(preprocess.read_text())
    frames = data.get("frames", [])
    print(f"Total preprocess frames: {len(frames)}")
    sharpness = [f["sharpness"] for f in frames if "sharpness" in f]
    motion = [f["motion_px"] for f in frames if "motion_px" in f]
    masked = [f["masked_fraction"] for f in frames if "masked_fraction" in f]
    import statistics
    print(f"Sharpness: min={min(sharpness):.0f} mean={statistics.mean(sharpness):.0f} max={max(sharpness):.0f}")
    print(f"Motion_px: min={min(motion):.1f} mean={statistics.mean(motion):.1f} max={max(motion):.1f}")
    print(f"Masked: min={min(masked):.3f} mean={statistics.mean(masked):.3f} max={max(masked):.3f}")

# Count originals
if fv_orig.exists():
    imgs = list(fv_orig.iterdir())
    print(f"Extracted frames: {len(imgs)}, resolution check:")
    if imgs:
        from PIL import Image
        im = Image.open(imgs[0])
        print(f"  Resolution: {im.size}")

# Check GPS in FAST_VALIDATION inputs
gps = fv_inputs / "gps.csv"
if gps.exists():
    import csv
    rows = list(csv.reader(gps.open()))
    print(f"GPS rows: {len(rows)}, header: {rows[0] if rows else 'EMPTY'}")
    print(f"First: {rows[1] if len(rows)>1 else 'NONE'}")
else:
    print("GPS file: NOT FOUND")

flight_meta = fv_inputs / "flight_metadata.json"
if flight_meta.exists():
    print("flight_metadata.json:", json.loads(flight_meta.read_text()))
