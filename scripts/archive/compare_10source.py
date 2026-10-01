import numpy as np
from pathlib import Path

dense_dir_6 = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_full_ref2")
dense_dir_10 = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_10_source_test")

def read_depth(path):
    with open(path, "rb") as f: data = f.read()
    idx = -1
    for i in range(3): idx = data.find(b"&", idx + 1)
    return np.frombuffer(data[idx+1:], dtype=np.float32)

maps_10 = sorted(list((dense_dir_10 / "stereo/depth_maps").glob("*.geometric.bin")))
frac_10 = [(read_depth(m) > 0).sum() / len(read_depth(m)) for m in maps_10]
names = [m.name for m in maps_10]

frac_6 = []
for n in names:
    m = dense_dir_6 / "stereo/depth_maps" / n
    if m.exists():
        arr = read_depth(m)
        frac_6.append((arr > 0).sum() / len(arr))

print(f"Comparison on {len(names)} maps:")
print(f"6-source Median: {np.median(frac_6):.3f}")
print(f"10-source Median: {np.median(frac_10):.3f}")
