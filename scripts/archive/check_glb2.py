import json, struct
from pathlib import Path

glb_path = "demo/mars_hkairport01_quality/mesh.glb"
with open(glb_path, 'rb') as f:
    f.read(12)  # header
    chunk_json_len = struct.unpack('<I', f.read(4))[0]
    f.read(4)  # chunk type
    chunk_json = f.read(chunk_json_len)
    gltf = json.loads(chunk_json)

print("Materials:", len(gltf.get('materials', [])))
print("Images:", len(gltf.get('images', [])))
print("Textures:", len(gltf.get('textures', [])))
print("Meshes:", len(gltf.get('meshes', [])))

for m in gltf.get('materials', []):
    print("  Material:", json.dumps(m)[:200])

for img in gltf.get('images', []):
    print("  Image:", json.dumps(img)[:200])
