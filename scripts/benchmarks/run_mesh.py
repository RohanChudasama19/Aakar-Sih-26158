import time
from pathlib import Path
import trimesh
import subprocess

work = Path('data/ab067831-368b-4087-a43e-11a08ee0ae74/work/test_B/dense_v1')
fused_ply = work / 'fused.ply'
mesh_out = work / 'meshed.ply'

print('Loading mesh...')
m = trimesh.load(str(mesh_out))
vertices = len(m.vertices)
faces = len(m.faces)

print('Connected components...')
t0 = time.time()
components = trimesh.graph.connected_components(m.edges)
cc_time = time.time() - t0

largest_verts = max(len(c) for c in components) if len(components) > 0 else vertices
lcc_fraction = largest_verts / max(1, vertices)

print(f'Mesh time: 0s')
print(f'Vertices: {vertices}')
print(f'Faces: {faces}')
print(f'Connected components: {len(components)}')
print(f'Largest component fraction: {lcc_fraction*100:.1f}%')
