import os
import shutil
import sqlite3
import hashlib
from pathlib import Path

# 1. Backup DB
db_path = Path("app/aerorecon.db")
if db_path.exists():
    shutil.copy2(db_path, "app/aerorecon.db.cleanup.bak")
    print("DB Backed up to app/aerorecon.db.cleanup.bak")

# 2. Inventory Storage
data_dir = Path("data").resolve()
print(f"DATA_DIR: {data_dir}")

def get_size(p):
    total = 0
    for dirpath, _, filenames in os.walk(p):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total += os.path.getsize(fp)
    return total

mars_dir = data_dir / "mars_hkairport01_quality"
mars_images_dir = mars_dir / "inputs/images"
mars_frames = list(mars_images_dir.glob("*")) if mars_images_dir.exists() else []

print(f"MARS images found: {len(mars_frames)}")

# Find candidates
candidates = []
for d in data_dir.iterdir():
    if not d.is_dir(): continue
    if d.name == "mars_hkairport01_quality":
        continue
    
    sz = get_size(d)
    
    # Check for MARS inputs just to be absolutely sure
    has_mars_frames = False
    cand_img_dir = d / "inputs/images"
    if cand_img_dir.exists():
        if len(list(cand_img_dir.glob("*"))) == len(mars_frames) and len(mars_frames) > 0:
            # might be a copy of mars
            has_mars_frames = True
            
    candidates.append({
        "path": d,
        "name": d.name,
        "size_bytes": sz,
        "has_mars_frames": has_mars_frames
    })

print("=== CLEANUP CANDIDATES ===")
total_reclaimable = 0
for c in candidates:
    if c['has_mars_frames']:
        print(f"PROTECTED (Suspected MARS copy): {c['name']}")
    else:
        sz_mb = c['size_bytes'] / (1024**2)
        print(f"DELETE_APPROVED: {c['name']} - {sz_mb:.2f} MB")
        total_reclaimable += c['size_bytes']

print(f"Total reclaimable: {total_reclaimable / (1024**3):.2f} GB")
