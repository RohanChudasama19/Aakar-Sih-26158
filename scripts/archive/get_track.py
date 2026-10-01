import sys
from pathlib import Path

sparse_dir = Path("data/test_dense_fix_3/work/sparse_txt")
if not sparse_dir.exists():
    print("Not ready")
    sys.exit(0)

# track lengths
track_lengths = []
with open(sparse_dir / "points3D.txt") as f:
    for line in f:
        if line.startswith("#"): continue
        parts = line.split()
        if len(parts) >= 8:
            track_length = (len(parts) - 8) // 2
            track_lengths.append(track_length)

import statistics
if track_lengths:
    print(f"Mean track length: {statistics.mean(track_lengths):.2f}")
    print(f"Median track length: {statistics.median(track_lengths):.2f}")
else:
    print("No tracks found")
