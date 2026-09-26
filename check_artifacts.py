from pathlib import Path
import json

# Check if MARS-LVIG has any existing sparse or dense reconstruction
mars = Path("data_external/mars_lvig")

found_anything = False
for ext in ["*.ply", "*.glb", "cameras.bin", "images.bin", "points3D.bin"]:
    for f in mars.rglob(ext):
        print(f"ARTIFACT: {f} size={f.stat().st_size}")
        found_anything = True

if not found_anything:
    print("No existing reconstruction artifacts found in mars_lvig.")

# Check test_benchmark sparse
bench = Path("data/test_benchmark")
for ext in ["*.ply", "*.glb"]:
    for f in bench.rglob(ext):
        print(f"BENCHMARK ARTIFACT: {f} size={f.stat().st_size}")

# Inspect benchmark sparse colmap model
import struct
sparse = bench / "work" / "sparse" / "0"
if sparse.exists():
    # Try to count registered images from images.bin
    images_bin = sparse / "images.bin"
    if images_bin.exists():
        with open(images_bin, 'rb') as f:
            num_images = struct.unpack('<Q', f.read(8))[0]
        print(f"Benchmark registered images: {num_images}")
