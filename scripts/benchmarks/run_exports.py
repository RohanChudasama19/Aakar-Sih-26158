import time
from pathlib import Path
from app.pipeline.mesh import build_mesh
from app.pipeline.exports import export_all
import app.schemas as schemas
from typing import Dict, Any

work = Path('data/ab067831-368b-4087-a43e-11a08ee0ae74/work')
test_b_dense = work / 'test_B' / 'dense_v1'
info = {'frames': []}
meta = {'camera': {'make': 'DJI', 'model': 'Mavic 3'}}
camera = schemas.intrinsics(meta, 1600, 900, None)
opts = {'profile': 'FAST_QUALITY'}

print('Building mesh...')
t0 = time.time()
mesh_report = build_mesh(test_b_dense, info, camera, lambda p, m: print(m), opts)
t_mesh = time.time() - t0

georef = {'metric_state': 'RELATIVE', 'transform': [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]}

print('Exporting...')
t0 = time.time()
export_report = export_all(work, info, camera, georef, mesh_report, lambda p, m: print(m), opts)
t_exp = time.time() - t0

print(f'Mesh time: {t_mesh:.1f}s')
print(f'Export time: {t_exp:.1f}s')
print(f'Total Post-Dense: {t_mesh + t_exp:.1f}s')
