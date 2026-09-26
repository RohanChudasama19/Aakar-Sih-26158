# PHASE 1: Check pipeline input compatibility
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

# Check what the API runner expects as input
import inspect
from app.pipeline import runner

print("=== runner.py signature ===")
src = inspect.getsource(runner)
# Find input handling
for i, line in enumerate(src.splitlines()):
    if any(kw in line for kw in ['video', 'frames', 'images_dir', 'input_mode', 'source_path', 'frame_dir', 'image_dir', 'upload']):
        print(f"L{i}: {line.rstrip()}")
