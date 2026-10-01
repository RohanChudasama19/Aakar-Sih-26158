from pathlib import Path

fast_dir = Path("data_external/mars_lvig/processed/HKairport01/FAST")
images_dir = fast_dir / "images"

img_list = sorted(images_dir.iterdir()) if images_dir.exists() else []
print(f"Images count: {len(img_list)}")
if img_list:
    import os
    sizes = [os.path.getsize(p) for p in img_list[:5]]
    print(f"First 5 image sizes (bytes): {sizes}")
    print(f"First 5 names: {[p.name for p in img_list[:5]]}")
    print(f"Last name: {img_list[-1].name}")

# Check GPS
import csv
with open(fast_dir / "gps.csv") as f:
    lines = list(csv.reader(f))
print(f"GPS rows: {len(lines)}")
print(f"GPS header: {lines[0] if lines else 'EMPTY'}")
print(f"First data row: {lines[1] if len(lines)>1 else 'NONE'}")
print(f"Last row: {lines[-1] if lines else 'NONE'}")
