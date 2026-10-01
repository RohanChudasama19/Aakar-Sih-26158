import sys, json, hashlib, shutil, time
from pathlib import Path
import numpy as np

work = Path("data/mars_hkairport01_quality/work")
dense_dir = work / "dense_mars"
demo_dir = Path("demo/mars_hkairport01_quality")

# Copy the new properly textured GLB
glb_src = dense_dir / "mesh_textured.glb"
glb_dst = demo_dir / "mesh.glb"
shutil.copy2(str(glb_src), str(glb_dst))
print(f"GLB updated: {glb_dst.stat().st_size:,} bytes")

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

# Update manifest with new GLB hash
manifest_file = demo_dir / "manifest.json"
manifest = json.loads(manifest_file.read_text())
manifest["artifacts"]["mesh_glb"]["size_bytes"] = glb_dst.stat().st_size
manifest["artifacts"]["mesh_glb"]["sha256"] = sha256(glb_dst)

manifest_file.write_text(json.dumps(manifest, indent=2))
print("manifest updated")
