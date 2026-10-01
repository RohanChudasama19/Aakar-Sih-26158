import time
import subprocess
from pathlib import Path

work = Path('data/ab067831-368b-4087-a43e-11a08ee0ae74/work/test_B/dense_v1')

def run_fusion(cache, threads):
    out_ply = work / f'fused_{cache}_{threads}.ply'
    cmd = [
        r'C:\\Tools\\COLMAP\\bin\\colmap.exe', 'stereo_fusion',
        '--workspace_path', str(work),
        '--workspace_format', 'COLMAP',
        '--input_type', 'photometric',
        '--output_path', str(out_ply),
        '--StereoFusion.min_num_pixels', '4',
        '--StereoFusion.cache_size', str(cache)
    ]
    if threads > 0:
        # Check if threads is supported or maybe we rely on openmp
        # Actually colmap stereo_fusion does not have a num_threads flag directly, but let's check
        pass
    
    t0 = time.time()
    subprocess.run(cmd, check=True)
    return time.time() - t0

# 32GB is default. Let's try 32, 16, 8.
for cache in [8, 16, 32]:
    print(f'Testing cache_size={cache}GB...')
    elapsed = run_fusion(cache, 0)
    print(f'Cache {cache}GB: {elapsed:.1f}s')
