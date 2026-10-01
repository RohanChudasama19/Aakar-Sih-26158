import hashlib
from pathlib import Path
import json

exp_dir = Path("data/95f51b12-b771-47bf-9201-c3700f9475a7/work/dense_experiment")

files_to_hash = [
    "fused_min4.ply",
    "fused_min2.ply",
    "mesh_min4.ply",
    "mesh_min2.ply",
    "screenshot_min4.png",
    "screenshot_min2.png"
]

manifest = {}
for f in files_to_hash:
    p = exp_dir / f
    if p.exists():
        manifest[f] = {
            "size": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest()
        }

with open(exp_dir / "experiment_manifest.json", "w") as out:
    json.dump(manifest, out, indent=2)

print(json.dumps(manifest, indent=2))
