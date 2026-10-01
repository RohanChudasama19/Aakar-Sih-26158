import hashlib, json
from pathlib import Path

def sha256(p):
    h = hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda: f.read(65536), b''): h.update(c)
    return h.hexdigest()

demo = Path('demo/mars_hkairport01_quality')
files = ['dense_cloud.ply','mesh.ply','mesh.glb','mesh_corrupted_backup.glb']
results = {}
for fn in files:
    p = demo / fn
    if p.exists():
        s = p.stat().st_size
        h = sha256(str(p))
        results[fn] = {'size': s, 'sha256': h}
        print(f'{fn}: {s:,} bytes  {h}')
    else:
        print(f'{fn}: MISSING')

import trimesh
m = trimesh.load(str(demo/'mesh.ply'), process=False, force='mesh')
g = trimesh.load(str(demo/'mesh.glb'), process=False, force='mesh')
glb_geom = next(iter(g.geometry.values())) if hasattr(g,'geometry') else g
print(f'mesh.ply faces: {len(m.faces)}')
print(f'mesh.glb faces: {len(glb_geom.faces)}')
print(f'Face count match: {len(m.faces)==len(glb_geom.faces)}')
