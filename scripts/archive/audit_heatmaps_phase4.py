import os
import json
import numpy as np
import trimesh

def check_mission(jid, glb_path):
    print(f"=== AUDITING {jid} ===")
    glb = trimesh.load(glb_path, force='mesh')
    num_faces = len(glb.faces)
    print(f"GLB Faces: {num_faces}")
    
    heatmap_dir = f"data/{jid}/work/outputs/heatmaps"
    for m in ['POINT_DENSITY', 'SURFACE_SUPPORT', 'POTENTIAL_CAMERA_VISIBILITY', 'RECONSTRUCTION_RISK', 'GEOMETRIC_ERROR']:
        meta_path = os.path.join(heatmap_dir, f"{m}.json")
        bin_path = os.path.join(heatmap_dir, f"{m}.bin")
        if not os.path.exists(meta_path):
            print(f"  {m}: MISSING METADATA")
            continue
            
        with open(meta_path, 'r') as f:
            meta = json.load(f)
            
        if meta.get('status') in ('NOT_VERIFIED', 'UNAVAILABLE'):
            print(f"  {m}: {meta.get('status')} (No array expected)")
            if os.path.exists(bin_path):
                print(f"    WARNING: Binary file exists for unavailable metric!")
            continue
            
        if not os.path.exists(bin_path):
            print(f"  {m}: WARNING: Valid status but missing binary file!")
            continue
            
        arr = np.fromfile(bin_path, dtype=np.float32)
        shape_match = len(arr) == num_faces
        
        print(f"  {m}:")
        print(f"    Metadata faces: {meta.get('num_faces')}")
        print(f"    Array shape: {len(arr)}")
        print(f"    Matches GLB: {shape_match}")
        print(f"    Min: {meta.get('min'):.4f}, Med: {meta.get('median'):.4f}, Max: {meta.get('max'):.4f}")
        actual_min = np.nanmin(arr) if not np.all(np.isnan(arr)) else float('nan')
        actual_med = np.nanmedian(arr) if not np.all(np.isnan(arr)) else float('nan')
        actual_max = np.nanmax(arr) if not np.all(np.isnan(arr)) else float('nan')
        print(f"    Actual Min: {actual_min:.4f}, Med: {actual_med:.4f}, Max: {actual_max:.4f}")

check_mission('mars_hkairport01_quality', 'data/mars_hkairport01_quality/work/outputs/model.glb')
check_mission('95f51b12-b771-47bf-9201-c3700f9475a7', 'data/95f51b12-b771-47bf-9201-c3700f9475a7/work/outputs/model.glb')

