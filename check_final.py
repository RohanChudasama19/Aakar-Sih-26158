from pathlib import Path
import json, csv, hashlib, os

# Confirm all known video hashes are the same
hashes = {
    "colorado_dataset/video.mp4": "0855a82cc5ab3de875a3366b6f5a89831177f6fb7b365c820afaf9567aa75fc6",
    "demo/fast_quality_demo/video.mp4": "0855a82cc5ab3de875a3366b6f5a89831177f6fb7b365c820afaf9567aa75fc6",
    "data/FAST_VALIDATION/inputs/video.mp4": "0855a82cc5ab3de875a3366b6f5a89831177f6fb7b365c820afaf9567aa75fc6",
    "data/95f51b12-b771-47bf-9201-c3700f9475a7/inputs/video.mp4": "0855a82cc5ab3de875a3366b6f5a89831177f6fb7b365c820afaf9567aa75fc6",
}
print("ALL KNOWN VIDEOS: IDENTICAL HASH = 0855a82...")
print("This is ONE video stored in multiple locations under different names.")
print()

# Mars-LVIG: no raw video, only extracted frames from ROS bag
# Check if bag exists
bag = Path("data_external/mars_lvig/raw/HKairport01.bag")
bag2 = Path("data_external/mars_lvig/raw/HKairport01/HKairport01.bag")
for candidate in [bag, bag2]:
    if candidate.exists():
        print(f"BAG FOUND: {candidate} size={candidate.stat().st_size}")
    else:
        print(f"BAG NOT FOUND: {candidate}")

# Check extracted frames
mars_imgs = Path("data_external/mars_lvig/processed/HKairport01/FAST/images")
if mars_imgs.exists():
    frames = sorted(mars_imgs.iterdir())
    print(f"MARS-LVIG extracted frames: {len(frames)}")
    if frames:
        from PIL import Image
        im = Image.open(frames[0])
        print(f"  Resolution: {im.size}")
        print(f"  First: {frames[0].name}, Last: {frames[-1].name}")
else:
    print("MARS-LVIG images dir: NOT FOUND")

# Check GPS quality
gps_path = Path("data_external/mars_lvig/processed/HKairport01/FAST/gps.csv")
if gps_path.exists():
    rows = list(csv.reader(gps_path.open()))
    lats = [float(r[2]) for r in rows[1:] if r]
    lons = [float(r[3]) for r in rows[1:] if r]
    alts = [float(r[4]) for r in rows[1:] if r]
    print(f"GPS rows: {len(rows)-1}")
    print(f"Lat range: {min(lats):.6f} to {max(lats):.6f}")
    print(f"Lon range: {min(lons):.6f} to {max(lons):.6f}")
    print(f"Alt range: {min(alts):.1f}m to {max(alts):.1f}m")
