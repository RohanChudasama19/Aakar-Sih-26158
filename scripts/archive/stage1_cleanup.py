import os
import shutil
import ctypes
import time
from pathlib import Path

def get_free_space(folder):
    free_bytes = ctypes.c_ulonglong(0)
    total_bytes = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, ctypes.pointer(total_bytes), ctypes.pointer(free_bytes))
    return free_bytes.value

def dir_size(path):
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                try: total += os.path.getsize(fp)
                except: pass
    return total

p = Path(r"C:\Users\ATHARAV\Documents\sih 26\gpt 6 astra\AeroRecon-SIH26158-Surface-Fix\aerorecon")
data_dir = p / "data"

free_before = get_free_space("C:\\")
print(f"BEFORE FREE: {free_before}")

targets = [
    "test_dense_fix_3",
    "final_fast_quality_demo",
    "359de0ec-8706-44ff-954f-fcc14f29a5ff"
]

deleted_stats = []
skipped_stats = []

for t in targets:
    tgt = data_dir / t
    
    if not tgt.exists():
        skipped_stats.append((str(tgt), "Directory does not exist"))
        continue
        
    canon = tgt.resolve()
    if not str(canon).startswith(str(data_dir.resolve())):
        skipped_stats.append((str(tgt), f"Canonical path {canon} outside data dir"))
        continue
        
    if tgt.is_symlink():
        skipped_stats.append((str(tgt), "Path is symlink"))
        continue
        
    sz = dir_size(tgt)
    # Delete
    try:
        shutil.rmtree(tgt)
        deleted_stats.append((str(tgt), sz, "Deleted successfully"))
    except Exception as e:
        skipped_stats.append((str(tgt), f"Deletion failed: {e}"))

time.sleep(2)
free_after = get_free_space("C:\\")
print(f"AFTER FREE: {free_after}")
print(f"RECOVERED: {free_after - free_before}")

active_job = data_dir / "95f51b12-b771-47bf-9201-c3700f9475a7"

protected_files = {
    "6-source dense": active_job / "work/dense_full_ref2/fused.ply",
    "10-source dense": active_job / "work/dense_10_source_full/fused.ply",
    "6-source mesh": active_job / "work/dense_full_ref2/mesh_raw.ply",
    "10-source mesh": active_job / "work/dense_10_source_full/mesh_raw.ply",
    "demo video": p / "demo/fast_quality_demo/video.mp4"
}

for k, path in protected_files.items():
    if path.exists():
        print(f"PROTECTED_OK {k}: {path} ({os.path.getsize(path)} bytes)")
    else:
        print(f"PROTECTED_MISSING {k}: {path}")

print("DELETED LIST:")
for d in deleted_stats:
    print(f"{d[0]} | {d[1]} | {d[2]}")
    
print("SKIPPED LIST:")
for s in skipped_stats:
    print(f"{s[0]} | {s[1]}")
