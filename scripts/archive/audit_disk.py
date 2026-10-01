import os
import ctypes
from pathlib import Path

def get_free_space(folder):
    free_bytes = ctypes.c_ulonglong(0)
    total_bytes = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, ctypes.pointer(total_bytes), ctypes.pointer(free_bytes))
    return total_bytes.value, total_bytes.value - free_bytes.value, free_bytes.value

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

tot, used, free = get_free_space("C:\\")
print(f"C: Total: {tot/1e9:.2f} GB")
print(f"C: Used: {used/1e9:.2f} GB")
print(f"C: Free: {free/1e9:.2f} GB")

dirs = ["data", "demo", "frontend", "web", "web_legacy_rc5", "tests", "logs", "imports", ".venv"]
print("\nPROJECT DIRECTORIES:")
for d in dirs:
    s = dir_size(p / d)
    print(f"{d} = {s/1e9:.3f} GB")

print("\nLARGEST JOBS:")
data_dir = p / "data"
if data_dir.exists():
    for job in data_dir.iterdir():
        if job.is_dir():
            s = dir_size(job)
            print(f"{job.name} = {s/1e9:.3f} GB")
            print(f"  - undistorted: {dir_size(job/'work/dense_fast_quality/images')/1e9:.3f} GB")
            print(f"  - dense_fast_quality stereo: {dir_size(job/'work/dense_fast_quality/stereo')/1e9:.3f} GB")
            print(f"  - dense_full_ref stereo: {dir_size(job/'work/dense_full_ref/stereo')/1e9:.3f} GB")
            print(f"  - dense_full_ref2 stereo: {dir_size(job/'work/dense_full_ref2/stereo')/1e9:.3f} GB")
            print(f"  - dense_10_source_full stereo: {dir_size(job/'work/dense_10_source_full/stereo')/1e9:.3f} GB")
            print(f"  - dense_10_source_test stereo: {dir_size(job/'work/dense_10_source_test/stereo')/1e9:.3f} GB")

print("\n30 LARGEST FILES:")
files = []
for dirpath, _, filenames in os.walk(p):
    if "node_modules" in dirpath or ".git" in dirpath or ".venv" in dirpath:
        continue
    for f in filenames:
        fp = os.path.join(dirpath, f)
        if not os.path.islink(fp):
            try: files.append((fp, os.path.getsize(fp)))
            except: pass

files.sort(key=lambda x: x[1], reverse=True)
for fp, sz in files[:30]:
    rel = os.path.relpath(fp, p)
    print(f"{rel} = {sz/1e6:.1f} MB")
