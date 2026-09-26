import hashlib, json
from pathlib import Path

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''): h.update(chunk)
    return h.hexdigest()

demo = Path("demo/mars_hkairport01_quality")
manifest_file = demo / "manifest.json"
manifest = json.loads(manifest_file.read_text())

glb = demo / "mesh.glb"
manifest["artifacts"]["mesh_glb"]["size_bytes"] = glb.stat().st_size
manifest["artifacts"]["mesh_glb"]["sha256"] = sha256(glb)

manifest_file.write_text(json.dumps(manifest, indent=2))
print("manifest updated")

for p in [demo/"dense_cloud.ply", demo/"mesh.ply", demo/"mesh.glb"]:
    print(f"{p.name}: {p.stat().st_size:,} bytes | {sha256(p)}")
