from pathlib import Path
import hashlib, json

p = Path("data_external/mars_lvig/raw/HKairport01/reference/cloud_merged.ply")
print(f"Reference point cloud: {p}")
print(f"Size: {p.stat().st_size:,} bytes ({p.stat().st_size/1024/1024:.1f} MB)")

# Quick hash
h = hashlib.sha256()
with open(p, 'rb') as f:
    for chunk in iter(lambda: f.read(65536), b''):
        h.update(chunk)
print(f"SHA256: {h.hexdigest()}")

# Count points
with open(p, 'rb') as f:
    header = b""
    while True:
        line = f.readline()
        header += line
        if b"end_header" in line:
            break

header_str = header.decode('utf-8', errors='ignore')
for line in header_str.splitlines():
    if 'element vertex' in line:
        print(f"PLY header vertex count: {line}")
    if 'element face' in line:
        print(f"PLY header face count: {line}")
    if 'property' in line[:20]:
        print(f"  {line}")
