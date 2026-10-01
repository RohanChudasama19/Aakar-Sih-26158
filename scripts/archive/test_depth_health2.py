import numpy as np
from pathlib import Path
import struct

dense_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_fast_quality")
depth_dir = dense_dir / "stereo/depth_maps"

photo_maps = list(depth_dir.glob("*.photometric.bin"))
geom_maps = list(depth_dir.glob("*.geometric.bin"))

def analyze_maps(maps):
    valid_fractions = []
    near_empty = 0
    for m in maps:
        with open(m, "rb") as f:
            data = f.read()
        
        # find the 3rd ampersand
        idx = -1
        for i in range(3):
            idx = data.find(b"&", idx + 1)
        
        floats_data = data[idx+1:]
        floats = np.frombuffer(floats_data, dtype=np.float32)
        valid = (floats > 0).sum()
        total = len(floats)
        frac = valid / max(1, total)
        valid_fractions.append(frac)
        if frac < 0.05:
            near_empty += 1
            
    if not valid_fractions: return 0, 0, 0
    return np.min(valid_fractions), np.median(valid_fractions), near_empty

p_min, p_med, p_emp = analyze_maps(photo_maps)
g_min, g_med, g_emp = analyze_maps(geom_maps)

print(f"Photometric maps: {len(photo_maps)}")
print(f"Photometric valid fraction: min={p_min:.3f}, median={p_med:.3f}")
print(f"Photometric near-empty: {p_emp}")

print(f"Geometric maps: {len(geom_maps)}")
print(f"Geometric valid fraction: min={g_min:.3f}, median={g_med:.3f}")
print(f"Geometric near-empty: {g_emp}")
