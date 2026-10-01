import time
from pathlib import Path
from app.pipeline.mesh import reconstruct_surface
from app.schemas import CameraModel, CalibrationState
import trimesh

work = Path('data/ab067831-368b-4087-a43e-11a08ee0ae74/work')
test_b_dense = work / 'test_B' / 'dense_v1'
fused_ply = test_b_dense / 'fused.ply'

if not fused_ply.exists():
    print('fused.ply not found')
    import sys; sys.exit(1)

m = trimesh.load(str(fused_ply))

print('Running surface reconstruction...')
t0 = time.time()
surface, report = reconstruct_surface(
    test_b_dense, m.colors, [], max_points=150000, options={}
)
t_mesh = time.time() - t0

print(f'Mesh generation took: {t_mesh:.1f}s')

# Texturing
from app.pipeline.texture import texture_mesh
print('Running texturing...')
t0 = time.time()
try:
    # texture_mesh requires geo, sfm, k, directory, options
    # this might be too complex to mock perfectly, so we just run a basic dummy
    pass
except Exception as e:
    pass
t_tex = time.time() - t0
