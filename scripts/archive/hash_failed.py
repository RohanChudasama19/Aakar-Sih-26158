import hashlib
from pathlib import Path
p = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/inputs/video.mp4")
if p.exists():
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    print(f"Failed mission hash: {h.hexdigest()}")
else:
    print("Failed mission video not found")
