import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
import inspect
from app.pipeline import runner, colmap as colmap_mod

# Find the SFM execution function name
src = inspect.getsource(runner)
fnames = [l.strip() for l in src.splitlines() if l.strip().startswith('def ')]
print("Functions in runner.py:", fnames)
print()
# Find colmap functions
src2 = inspect.getsource(colmap_mod)
fnames2 = [l.strip() for l in src2.splitlines() if l.strip().startswith('def ')]
print("Functions in colmap.py:", fnames2)
