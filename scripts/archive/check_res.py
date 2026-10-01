from pathlib import Path
from PIL import Image

work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
dense_dir = work_dir / "dense_10_source_full"

# check original image size
img = list((dense_dir / "images").iterdir())[0]
with Image.open(img) as im:
    print(f"Original image size: {im.size}")

# check patch-match.cfg
if (dense_dir / "stereo/patch-match.cfg").exists():
    print("patch-match.cfg exists.")

# read depth map header
depth_map = list((dense_dir / "stereo/depth_maps").glob("*.bin"))[0]
with open(depth_map, "rb") as f:
    width = int.from_bytes(f.read(4), "little")
    height = int.from_bytes(f.read(4), "little")
    depth = int.from_bytes(f.read(4), "little")
    print(f"Depth map dims: {width} x {height} x {depth}")
