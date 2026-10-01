import hashlib, json
from pathlib import Path
import trimesh, numpy as np

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''): h.update(chunk)
    return h.hexdigest()

demo = Path("demo/mars_hkairport01_quality")
artifacts = {
    "dense_cloud.ply": None,
    "mesh.ply": None,
    "mesh.glb": None,
}
for name in list(demo.glob("*")):
    sz = name.stat().st_size
    sh = sha256(name)
    print(f"{name.name:40s} {sz:>12,} bytes  {sh[:16]}...")

print()
ply = demo / "mesh.ply"
glb = demo / "mesh.glb"

print("--- PLY Geometry ---")
m = trimesh.load(str(ply), process=False)
print(f"  Vertices: {len(m.vertices):,}")
print(f"  Faces:    {len(m.faces):,}")
print(f"  Is watertight: {m.is_watertight}")
print(f"  Bounding box:  {np.round(m.bounds, 3).tolist()}")

print()
print("--- GLB Geometry ---")
g = trimesh.load(str(glb), process=False, force='mesh')
if hasattr(g, 'geometry'):
    for k,v in g.geometry.items():
        print(f"  [{k}] vertices={len(v.vertices):,} faces={len(v.faces):,}")
        if hasattr(v, 'visual') and hasattr(v.visual, 'uv'):
            print(f"       UVs={v.visual.uv is not None}")
else:
    print(f"  Vertices: {len(g.vertices):,}  Faces: {len(g.faces):,}")

cloud = demo / "dense_cloud.ply"
print()
print("--- Dense Cloud ---")
c = trimesh.load(str(cloud))
print(f"  Points: {len(c.vertices):,}")
print(f"  Is LiDAR reference (34M+): {len(c.vertices) > 10000000}")
