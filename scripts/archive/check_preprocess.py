import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
import inspect
from app.pipeline import preprocess

src = inspect.getsource(preprocess)
lines = src.splitlines()
# Find the extract function signature and first ~60 lines
for i, line in enumerate(lines):
    if 'def extract' in line:
        print(f"FOUND extract at L{i}:")
        for j in range(i, min(i+80, len(lines))):
            print(f"L{j}: {lines[j]}")
        break
