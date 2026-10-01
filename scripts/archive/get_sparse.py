import sys
from pathlib import Path

sparse = Path('data/b83295bd-9419-485c-bdee-8dce65de4f7c/work/test_sparse/points3D.txt')
if not sparse.exists():
    print("No points")
    exit(1)

total_raw = 0
filtered = 0
obs = 0
with open(sparse) as f:
    for line in f:
        if line.startswith('#'): continue
        parts = line.split()
        total_raw += 1
        
        # COLMAP points3D.txt: POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[]
        error = float(parts[7])
        track_len = (len(parts) - 8) // 2
        obs += track_len
        
        if error <= 2.0 and track_len >= 3:
            filtered += 1

print(f"raw observations: {obs}")
print(f"unique 3D points: {total_raw}")
print(f"production sparse count: {filtered}")
