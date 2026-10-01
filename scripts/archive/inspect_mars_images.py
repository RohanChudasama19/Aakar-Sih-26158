import os
from pathlib import Path
from collections import defaultdict

mars_dir = Path("data/mars_hkairport01_quality")
counts = defaultdict(int)

for p in mars_dir.rglob("*.jpg"):
    counts[str(p.parent)] += 1

for dirpath, count in counts.items():
    print(f"{dirpath}: {count} JPGs")

