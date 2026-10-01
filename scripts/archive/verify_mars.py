from pathlib import Path
import json

mars_dir = Path("data/mars_hkairport01_quality")
outputs = mars_dir / "work/outputs"

print("=== MARS VERIFICATION ===")
glb = outputs / "model.glb"
print(f"GLB exists: {glb.exists()}, Size: {glb.stat().st_size / (1024**2):.2f} MB")

dense_rel = outputs / "cloud_relative.ply"
print(f"Dense relative exists: {dense_rel.exists()}, Size: {dense_rel.stat().st_size / (1024**2) if dense_rel.exists() else 0:.2f} MB")

report = outputs / "mission_report.json"
print(f"Report exists: {report.exists()}")

hm = outputs / "heatmaps/point_density.bin"
print(f"Heatmaps exist: {hm.exists()}")

frames = list((mars_dir / "work/dense_mars/images").glob("*.jpg"))
print(f"Frames exist: {len(frames)}")
