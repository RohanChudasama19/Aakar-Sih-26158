import os
import shutil
import ctypes
import time
import hashlib
import json
import csv
import struct
import numpy as np
from pathlib import Path

def get_free_space(folder):
    free_bytes = ctypes.c_ulonglong(0)
    total_bytes = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, ctypes.pointer(total_bytes), ctypes.pointer(free_bytes))
    return free_bytes.value

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(81920):
            h.update(chunk)
    return h.hexdigest()

def read_colmap_map(path):
    with open(path, "rb") as f:
        width = int(f.readline().strip().split(b"&")[1])
        height = int(f.readline().strip().split(b"&")[1])
        channels = int(f.readline().strip().split(b"&")[1])
        data = f.read()
    arr = np.frombuffer(data, dtype=np.float32)
    return width, height, channels, arr

free_before = get_free_space("C:\\")

p = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon")
work_dir = p / "data/95f51b12-b771-47bf-9201-c3700f9475a7/work"

diag_dir = work_dir / "preserved_dense_diagnostics"
diag_dir.mkdir(exist_ok=True)

targets = [
    "dense_full_ref2/stereo",
    "dense_10_source_full/stereo",
    "dense_fast_quality/stereo"
]

inventory = []
health = {}
deleted_stats = {}
total_near_empty = 0

print(f"Reading maps to generate inventory...")
t0 = time.time()

# We only sample the 10-source full for representative maps
representatives_chosen = []
candidates_10 = []

for tgt in targets:
    tgt_path = work_dir / tgt
    if not tgt_path.exists(): continue
    deleted_stats[tgt] = {"depth": 0, "normal": 0, "total": 0}
    
    for sub in ["depth_maps", "normal_maps"]:
        sub_dir = tgt_path / sub
        if not sub_dir.exists(): continue
        
        for f in sub_dir.iterdir():
            if not f.is_file() or not f.name.endswith(".bin"): continue
            
            sz = f.stat().st_size
            try:
                w, h, c, arr = read_colmap_map(f)
                valid = arr > 0
                valid_count = valid.sum()
                finite = np.isfinite(arr[valid])
                finite_count = finite.sum()
                if finite_count > 0:
                    min_d = float(np.min(arr[valid][finite]))
                    max_d = float(np.max(arr[valid][finite]))
                else:
                    min_d, max_d = 0.0, 0.0
                
                frac = valid_count / len(arr)
                finite_frac = finite_count / len(arr)
                is_near_empty = frac < 0.01
                if is_near_empty: total_near_empty += 1
                
                if tgt == "dense_10_source_full/stereo" and sub == "depth_maps" and f.name.endswith(".geometric.bin"):
                    candidates_10.append({
                        "name": f.name.split(".")[0],
                        "frac": frac,
                        "path": f
                    })
            except Exception as e:
                w, h, frac, finite_frac, min_d, max_d, is_near_empty = 0, 0, 0, 0, 0, 0, True
            
            sha = sha256_file(f)
            
            item = {
                "workspace": tgt.split("/")[0],
                "image": f.name.split(".")[0],
                "type": f.name.split(".")[1] if len(f.name.split(".")) > 1 else sub,
                "map": sub,
                "width": w, "height": h, "size": sz,
                "valid_frac": frac,
                "finite_frac": finite_frac,
                "min_d": min_d, "max_d": max_d,
                "near_empty": is_near_empty,
                "sha256": sha,
                "path": str(f)
            }
            inventory.append(item)
            health[str(f)] = item

print(f"Inventory completed in {time.time()-t0:.1f}s. Total maps: {len(inventory)}")

with open(diag_dir / "depth_map_inventory.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["workspace", "image", "type", "map", "width", "height", "size", "valid_frac", "finite_frac", "min_d", "max_d", "near_empty", "sha256", "path"])
    w.writeheader()
    w.writerows(inventory)

with open(diag_dir / "depth_map_health.json", "w") as f:
    json.dump({"total": len(inventory), "near_empty": total_near_empty, "maps": health}, f, indent=2)

# Select representatives
candidates_10.sort(key=lambda x: x["name"])
sel = []
if len(candidates_10) > 0:
    sel.append(candidates_10[0]["name"]) # early
    sel.append(candidates_10[len(candidates_10)//2]["name"]) # mid
    sel.append(candidates_10[-1]["name"]) # late
    candidates_10.sort(key=lambda x: x["frac"])
    if candidates_10[0]["name"] not in sel: sel.append(candidates_10[0]["name"]) # near empty
    if candidates_10[-1]["name"] not in sel: sel.append(candidates_10[-1]["name"]) # high support
    
    # Fill up to 5 if dupes
    for c in candidates_10:
        if len(sel) >= 5: break
        if c["name"] not in sel: sel.append(c["name"])

print(f"Preserving representative maps for: {sel}")
for name in sel:
    for ext in [".photometric.bin", ".geometric.bin"]:
        for mtype in ["depth_maps", "normal_maps"]:
            src = work_dir / "dense_10_source_full/stereo" / mtype / f"{name}{ext}"
            if src.exists():
                dst = diag_dir / f"{name}_{mtype}{ext}"
                shutil.copy2(src, dst)
                # verify
                if sha256_file(src) != sha256_file(dst):
                    print(f"Preservation failed for {src}")

# Delete binary maps securely
for tgt in targets:
    tgt_path = work_dir / tgt
    for sub in ["depth_maps", "normal_maps"]:
        sub_dir = tgt_path / sub
        if not sub_dir.exists(): continue
        for f in sub_dir.iterdir():
            if f.is_file() and f.name.endswith(".bin"):
                sz = f.stat().st_size
                f.unlink()
                deleted_stats[tgt][sub.split("_")[0]] += sz
                deleted_stats[tgt]["total"] += sz

    # mark workspace
    (tgt_path / "CLEANUP_MANIFEST.txt").write_text("Stage 2 Cleanup: Binary depth and normal maps removed. Workspace is NON-RESUMABLE.")

time.sleep(2)
free_after = get_free_space("C:\\")

# Verify
protected = [
    work_dir / "dense_full_ref2/fused.ply",
    work_dir / "dense_full_ref2/mesh_raw.ply",
    work_dir / "dense_10_source_full/fused.ply",
    work_dir / "dense_10_source_full/mesh_raw.ply",
    work_dir / "sparse",
    p / "demo/fast_quality_demo/video.mp4"
]
prot_status = {}
for pr in protected:
    prot_status[pr.name] = "INTACT" if pr.exists() else "MISSING"

print(f"BEFORE: {free_before}")
print(f"AFTER: {free_after}")
print(f"RECOVERED: {free_after - free_before}")
for t, d in deleted_stats.items():
    print(f"DEL: {t} | depth: {d['depth']} | normal: {d['normal']} | total: {d['total']}")
print("PROTECTED:")
for k,v in prot_status.items():
    print(f"{k}: {v}")
print(f"Total near empty: {total_near_empty}")
print(f"Inventory total: {len(inventory)}")
