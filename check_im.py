from PIL import Image
from pathlib import Path
work_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work")
im = Image.open(work_dir / "dense_10_source_full/images/000000.png")
print(f"Image size: {im.size}")
