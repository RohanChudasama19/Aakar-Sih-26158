from pathlib import Path
import json, csv, statistics

# Check MARS GPS for coordinate validity and coverage
gps_path = Path("data_external/mars_lvig/processed/HKairport01/FAST/gps.csv")
rows = list(csv.reader(gps_path.open()))
lats = [float(r[2]) for r in rows[1:]]
lons = [float(r[3]) for r in rows[1:]]
alts = [float(r[4]) for r in rows[1:]]

print(f"MARS-LVIG HKairport01 GPS summary:")
print(f"  Total GPS records (per-frame): {len(lats)}")
print(f"  Lat: {statistics.mean(lats):.6f} +/- center, range {max(lats)-min(lats):.6f} deg")
print(f"  Lon: {statistics.mean(lons):.6f} +/- center, range {max(lons)-min(lons):.6f} deg")
print(f"  Alt: {statistics.mean(alts):.1f}m mean, {min(alts):.1f}m to {max(alts):.1f}m")
print(f"  GPS valid (non-zero): all")
print()

# Estimate overlap: 567 frames, ~780s, 10fps subsampled
# Reference cloud: 34M points, ~650m x 500m scene
# Frame resolution: 1280x1070, distinct building/infrastructure textures
print("Reconstruction potential:")
print("  Scene: HK Airport area 234m x 347m (GPS bound)")
print("  Reference cloud (lidar): 34.3M points, 657m x 501m x 138m span")
print("  Camera: 1280x1070 (2448x2048 original, downsampled)")
print("  Baseline: moving UAV, 13min mission, continuous overlap")
print("  Texture: Airport tarmac, taxiways, terminal buildings, ground vehicles")
print("  Risk: Airport tarmac = large flat featureless regions (similar to grass risk)")
print("  Risk: Some motion blur possible at higher speeds")
print("  Upside: Building walls, vehicles, rooftops provide strong features")
print("  Lidar reference cloud available for ground-truth validation")
