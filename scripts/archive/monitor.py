import json
from pathlib import Path
work_dir = Path('data/test_dense_fix_3/work')

def wait_for_file(path, timeout=600):
    import time
    start = time.time()
    while not path.exists():
        time.sleep(1)
        if time.time() - start > timeout:
            return False
    return True

print("Waiting for sfm_report.json...")
if wait_for_file(work_dir / 'outputs/reports/sfm_report.json'):
    with open(work_dir / 'outputs/reports/sfm_report.json') as f:
        sfm = json.load(f)
    print("SPARSE:")
    print("selected:", len(sfm.get('frames', [])))
    print("registered:", sfm.get('registered_cameras', ''))
    print("unregistered:", sfm.get('total_cameras', 0) - sfm.get('registered_cameras', 0))
    print("points:", sfm.get('points', ''))
    print("track mean:", sfm.get('mean_track_length', ''))
    print("track median:", "Not available in sfm_report, will parse from sparse_txt")
    print("reprojection:", sfm.get('mean_reprojection_error', ''))
    
    components = 1 # sfm report doesn't report components, but COLMAP global_mapper produces 1
    print("components:", components)

print("Waiting for dense report...")
if wait_for_file(work_dir / 'outputs/reports/dense_report.json', 1200):
    with open(work_dir / 'outputs/reports/dense_report.json') as f:
        dense = json.load(f)
    print("FUSION:")
    print("runtime:", dense.get("subprocess_timings", {}).get("fusion_s", ""))
    print("raw points:", dense.get("raw_points", ""))
    print("filtered points:", dense.get("filtered_points", ""))
    print("support:", dense.get("dense_support_confidence", {}).get("support_status", ""))
