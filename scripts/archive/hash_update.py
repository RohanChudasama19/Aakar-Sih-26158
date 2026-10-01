import hashlib
import json
from pathlib import Path

demo_dir = Path("demo/degraded_fast_quality")
manifest_file = demo_dir / "manifest.json"

if manifest_file.exists():
    with open(manifest_file, "r") as f:
        manifest = json.load(f)
else:
    manifest = {"sha256_hashes": {}}

for p in demo_dir.glob("*.*"):
    if p.is_file() and p.name != "manifest.json":
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        manifest["sha256_hashes"][p.name] = h

with open(manifest_file, "w") as f:
    json.dump(manifest, f, indent=2)

manifest_hash = hashlib.sha256(manifest_file.read_bytes()).hexdigest()
print("Manifest updated.")
print(f"Manifest Hash: {manifest_hash}")
for k, v in manifest["sha256_hashes"].items():
    print(f"{k}: {v}")
