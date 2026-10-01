from app.pipeline.heatmap_engine import generate_mission_heatmaps
from app.config import DATA
import os
import json

print("=== MARS ===")
res_mars = generate_mission_heatmaps("mars_hkairport01_quality", str(DATA))
print(res_mars)

if res_mars['status'] == 'success':
    out_dir = os.path.join(DATA, "mars_hkairport01_quality", "work", "outputs", "heatmaps")
    with open(os.path.join(out_dir, "SURFACE_SUPPORT.json")) as f:
        m = json.load(f)
        print("MARS SUPPORT:", m['min'], m['max'], m['median'])

print("\n=== COLORADO ===")
res_col = generate_mission_heatmaps("95f51b12-b771-47bf-9201-c3700f9475a7", str(DATA))
print(res_col)

if res_col['status'] == 'success':
    out_dir = os.path.join(DATA, "95f51b12-b771-47bf-9201-c3700f9475a7", "work", "outputs", "heatmaps")
    with open(os.path.join(out_dir, "SURFACE_SUPPORT.json")) as f:
        m = json.load(f)
        print("COLORADO SUPPORT:", m['min'], m['max'], m['median'])
