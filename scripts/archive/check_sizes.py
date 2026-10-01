import trimesh
import numpy as np

for f in ['demo/mars_hkairport01_quality/mesh.glb', 'demo/degraded_fast_quality/mesh_textured.glb']:
    m = trimesh.load(f, force='mesh')
    bbox = m.bounding_box.extents
    print(f, 'size:', np.linalg.norm(bbox))
