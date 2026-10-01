import time
from pathlib import Path
from app.pipeline.sfm_backend import execute_sfm
import app.schemas as schemas

work = Path('data/test_benchmark/work')
frames_dir = work / 'frames'
opts = {'profile': 'FAST_QUALITY'}

meta = {'camera': {'make': 'DJI', 'model': 'Mavic 3'}}
camera = schemas.intrinsics(meta, 1600, 900, None)

info = {'frames': [{'name': p.name} for p in sorted(frames_dir.glob('*.png'))]}

start = time.time()
res = execute_sfm(frames_dir, info, camera, lambda p, msg: print(f'[{p}%] {msg}'), force_cpu=False, options=opts)
elapsed = time.time() - start

print('SPARSE RESULT')
print(f'Runtime: {elapsed:.1f}s')
print(f'Registered: {res["sfm_report"]["registered_cameras"]}')
print(f'Points: {res["sfm_report"]["sparse_point_count"]}')
print(f'Reprojection: {res["sfm_report"]["mean_reprojection_error_px"]}')
