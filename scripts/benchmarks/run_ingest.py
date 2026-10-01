import time
from pathlib import Path
from app.pipeline.preprocess import extract
import json

video = Path('colorado_dataset/video.mp4')
work = Path('data/test_benchmark/work')
work.mkdir(parents=True, exist_ok=True)
frames_dir = work / 'frames'
opts = {'profile': 'FAST_QUALITY', 'max_frames': 250, 'max_width': 1600}

start = time.time()
ready_report, info = extract(video, frames_dir, opts, [], {}, None, lambda p, msg: print(msg))
elapsed = time.time() - start

print('\nFAST_QUALITY VALIDATION - VIDEO INGEST')
print(f'source frames: {info["input_frames"]}')
print(f'visited: {info["decoded_frames"]}')
print(f'evaluated: {info["candidate_count"]}')
print(f'retained: {len(info["frames"])}')
print(f'decode passes: 1')
print(f'runtime: {elapsed:.2f}s')
print(f'Readiness Status: {ready_report["status"]}')
print(f'Blocking reasons: {ready_report.get("blocking_reasons")}')
