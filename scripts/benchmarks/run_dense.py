import time
import subprocess
from pathlib import Path
import numpy as np
import trimesh

work = Path('data/test_benchmark/work')
sparse_dir = work / 'sparse' / '0'

def run_cmd(cmd):
    start = time.time()
    subprocess.run(cmd, check=True)
    return time.time() - start

for count in [140, 120, 105]:
    dense_dir = work / f'dense_{count}'
    dense_dir.mkdir(exist_ok=True)
    
    print(f'\n--- DENSE TEST {count} ---')
    print('Undistorting...')
    run_cmd([
        r'C:\\Tools\\COLMAP\\bin\\colmap.exe', 'image_undistorter',
        '--image_path', str(work / 'frames'),
        '--input_path', str(sparse_dir),
        '--output_path', str(dense_dir),
        '--output_type', 'COLMAP',
        '--max_image_size', '1600'
    ])
    
    # Generate patch-match.cfg
    images = sorted(list((dense_dir / 'images').glob('*.png')))
    target = count
    indices = np.linspace(0, len(images) - 1, target, dtype=int)
    selected = [images[i].name for i in indices]
    
    cfg_path = dense_dir / 'stereo' / 'patch-match.cfg'
    cfg_path.parent.mkdir(exist_ok=True)
    with open(cfg_path, 'w') as f:
        for name in selected:
            f.write(f'{name}\n__auto__, 6\n')
            
    print('PatchMatch...')
    pm_time = run_cmd([
        r'C:\\Tools\\COLMAP\\bin\\colmap.exe', 'patch_match_stereo',
        '--workspace_path', str(dense_dir),
        '--workspace_format', 'COLMAP',
        '--PatchMatchStereo.max_image_size', '1600',
        '--PatchMatchStereo.geom_consistency', '1',
        '--PatchMatchStereo.window_radius', '4',
        '--PatchMatchStereo.window_step', '2',
        '--PatchMatchStereo.num_iterations', '3'
    ])
    
    print('Fusion...')
    fusion_time = run_cmd([
        r'C:\\Tools\\COLMAP\\bin\\colmap.exe', 'stereo_fusion',
        '--workspace_path', str(dense_dir),
        '--workspace_format', 'COLMAP',
        '--input_type', 'photometric', # Fallback to photometric since geom is skipped due to patch-match.cfg or bug
        '--output_path', str(dense_dir / 'fused.ply'),
        '--StereoFusion.min_num_pixels', '4'
    ])
    
    try:
        pc = trimesh.load(str(dense_dir / 'fused.ply'))
        pts = len(pc.vertices)
    except:
        pts = 0
        
    print(f'Test {count}: PatchMatch: {pm_time:.1f}s, Fusion: {fusion_time:.1f}s, Points: {pts}')
