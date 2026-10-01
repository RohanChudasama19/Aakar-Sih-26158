import os
import subprocess
from pathlib import Path
import statistics

sparse = Path('data/b83295bd-9419-485c-bdee-8dce65de4f7c/work/test_sparse')
if not sparse.exists() or not (sparse / 'images.bin').exists():
    print("Wait for sparse")
    exit(0)

print("Converting...")
subprocess.run(['C:\\Tools\\COLMAP\\bin\\colmap.exe', 'model_converter', '--input_path', str(sparse), '--output_path', str(sparse), '--output_type', 'TXT'], check=True)

lengths = []
with open(sparse / 'points3D.txt') as f:
    for line in f:
        if line.startswith('#'): continue
        parts = line.split()
        length = (len(parts) - 8) // 2
        lengths.append(length)

print(f"Points: {len(lengths)}")
print(f"Mean track: {statistics.mean(lengths):.2f}")
print(f"Median track: {statistics.median(lengths):.2f}")
