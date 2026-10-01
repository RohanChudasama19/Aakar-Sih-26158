import json
from pathlib import Path

jid = '95f51b12-b771-47bf-9201-c3700f9475a7'
rep = json.loads(Path(f'data/{jid}/work/outputs/mission_report.json').read_text())

pre = rep['preprocessing']
sfm = rep['sfm']
dense = rep['dense']
mesh = rep.get('mesh', {})
exp = rep.get('exports', {})
stages = rep.get('stages', {})
total = sum(v['elapsed_sec'] for v in stages.values())

print('=== PRODUCTION VIDEO PIPELINE EVIDENCE (Colorado job) ===')
print(f'Video: {pre["width"]}x{pre["height"]} @ {pre["fps"]:.2f}fps  duration={pre["duration_sec"]:.1f}s')
print(f'Decoded keyframes: {pre["decoded_frames"]}/{pre["input_frames"]}  blur_rejections={pre["blur_rejections"]}')
print(f'SfM: {sfm["backend"]}  registered={sfm["registered_cameras"]}/{sfm["input_frames"]}  sparse_pts={sfm["sparse_point_count"]}')
print(f'SfM reprojection: {sfm["mean_reprojection_error_px"]:.3f} px mean')
print(f'Dense: {dense["backend"]}  raw={dense["raw_points"]}  filtered={dense["filtered_points"]}')
print(f'Mesh: {mesh.get("mesh_backend")}  faces={mesh.get("faces")}  texture={mesh.get("texture_status")}')
print(f'Metric state: {rep.get("metric_state")}')
print(f'Total runtime: {total:.0f}s = {total/60:.1f} min')
print('Exports:', list(exp.get('generated_files', {}).keys()))
