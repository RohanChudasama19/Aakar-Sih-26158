import hashlib
import json
from pathlib import Path

def get_hash(path):
    if not path.exists(): return None
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

roots = [
    Path("colorado_dataset"),
    Path("demo/fast_quality_demo"),
    Path("data_external/mars_lvig"),
    Path("data_external/usegeo"),
    Path("data/test_benchmark"),
    Path("data/FAST_VALIDATION")
]

results = {}
for root in roots:
    if root.exists():
        vids = list(root.rglob("*.mp4")) + list(root.rglob("*.MP4")) + list(root.rglob("*.mov")) + list(root.rglob("*.MOV"))
        for v in vids:
            results[str(v)] = {
                "size": v.stat().st_size,
                "hash": get_hash(v)
            }

print(json.dumps(results, indent=2))
